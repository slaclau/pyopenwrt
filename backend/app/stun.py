import asyncio
import enum
from ipaddress import IPv4Address
import logging
import socket
import uuid

from .routers.control.command import DeviceCommand
from .routers.status.status import DeviceStatus

logger = logging.getLogger(f"uvicorn.{__name__}")


class StunMessageType(enum.IntEnum):
    BindingRequest = 0x0001
    BindingResponse = 0x0101


class StunAttributeType(enum.IntEnum):
    MappedAddress = 0x0001


class StunAttribute:
    attribute_type: StunAttributeType
    value: bytes

    @property
    def length(self):
        return len(self.value)

    @classmethod
    def pop_from_bytes(cls, bytes_object: bytes) -> tuple["StunAttribute", bytes]:
        attribute_type = StunAttributeType.from_bytes(bytes_object[0:2])
        length = int.from_bytes(bytes_object[2:4])
        value = bytes_object[4 : 4 + length]
        bytes_object = bytes_object[4 : 4 + length :]
        match attribute_type:
            case StunAttributeType.MappedAddress:
                attribute = StunMappedAddress(value=value)

        return attribute, bytes_object

    def to_bytes(self):
        return self.attribute_type.to_bytes(2) + self.length.to_bytes(2) + self.value

    def __init__(self, value: bytes):
        self.value = value


class StunMappedAddress(StunAttribute):
    attribute_type = StunAttributeType.MappedAddress

    @classmethod
    def from_data(cls, address: IPv4Address | str, port: int):
        address_bytes = (
            socket.inet_aton(address)
            if isinstance(address, str)
            else int(address).to_bytes(4)
        )
        value = bytes([0, 1]) + port.to_bytes(2) + address_bytes
        return StunMappedAddress(value=value)


class StunMessage:
    message_type: StunMessageType
    session_id: bytes
    attributes: list[StunAttribute]

    def __init__(
        self,
        message_type: StunMessageType,
        session_id: bytes,
        attributes: list[StunAttribute],
    ):
        self.message_type = message_type
        if len(session_id) != 12:
            raise ValueError(f"Invalid session id {session_id!r}")
        self.session_id = session_id
        self.attributes = attributes

    @property
    def length(self):
        return sum([attribute.length + 4 for attribute in self.attributes])

    @classmethod
    def from_bytes(cls, bytes_object: bytes):
        if not (
            bytes_object[4:8] == bytes([0x21, 0x12, 0xA4, 0x42])
            and (bytes_object[0] & 0b11000000 == 0)
        ):
            raise ValueError("Not a STUN message")
        attributes: list[StunAttribute] = []
        attributes_bytes = bytes_object[20:]
        while attributes_bytes:
            attribute, attributes_bytes = StunAttribute.pop_from_bytes(attributes_bytes)
            attributes.append(attribute)
        return cls(
            message_type=StunMessageType.from_bytes(bytes_object[0:2]),
            session_id=bytes_object[8:20],
            attributes=attributes,
        )

    def to_bytes(self):
        rtn = (
            self.message_type.to_bytes(2)
            + self.length.to_bytes(2)
            + bytes([0x21, 0x12, 0xA4, 0x42])
            + self.session_id
        )
        for attribute in self.attributes:
            rtn += attribute.to_bytes()

        return rtn

    def __repr__(self):
        return f"{self.message_type!r}: {self.attributes}"


class ControllerUDPProtocol(asyncio.DatagramProtocol):
    def connection_made(self, transport) -> None:
        self.transport = transport

    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        try:
            message = StunMessage.from_bytes(data)
        except ValueError:
            logger.warning(f"Unexpected data on stun port {data!r} from {addr}")

        match msg_type := message.message_type:
            case StunMessageType.BindingRequest:
                logger.info(f"got stun Binding Request from {addr}")
                mapped_address = StunMappedAddress.from_data(
                    address=addr[0], port=addr[1]
                )
                res = StunMessage(
                    message_type=StunMessageType.BindingResponse,
                    session_id=message.session_id,
                    attributes=[mapped_address],
                )
                self.transport.sendto(data=res.to_bytes(), addr=addr)
            case _:
                logger.warning(f"Unexpected stun message type {msg_type!r} from {addr}")


UDP_SOCKET = None


async def setup_stun_server() -> ControllerUDPProtocol:
    loop = asyncio.get_running_loop()

    transport, protocol = await loop.create_datagram_endpoint(
        lambda: ControllerUDPProtocol(), local_addr=("0.0.0.0", 3478)
    )
    global UDP_SOCKET
    UDP_SOCKET = transport
    return protocol


def send_immediate_command(device_id: uuid.UUID, command: DeviceCommand, session):
    status = session.get(DeviceStatus, device_id)
    if not status:
        raise RuntimeError
    addr = (str(status.nat_ip), status.nat_port)
    if UDP_SOCKET:
        UDP_SOCKET.sendto(data=bytes(command.value, "utf-8"), addr=addr)
    else:
        raise RuntimeError
