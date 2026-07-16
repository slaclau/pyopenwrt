import asyncio
import logging

logger = logging.getLogger(f"uvicorn.{__name__}")


class ControllerUDPProtocol(asyncio.DatagramProtocol):
    def connection_made(self, transport) -> None:
        self.transport = transport

    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        if data[4:8] == bytes([0x21, 0x12, 0xA4, 0x42]) and (data[0] & 0b11000000 == 0):
            length = int.from_bytes(data[2:4])
            assert length == 0
            match msg_type := data[0:2]:
                case b"\x00\x01":
                    print(f"stun req received from {addr}")
                    res = bytearray(data)
                    res[0] = 0x01
                    self.transport.sendto(data=res, addr=addr)
                    self.transport.sendto(data=b"inform", addr=addr)
                case _:
                    print(msg_type)
        else:
            print(f"got {data!r} from {addr}")


async def setup_stun_server() -> ControllerUDPProtocol:
    loop = asyncio.get_running_loop()

    _, protocol = await loop.create_datagram_endpoint(
        lambda: ControllerUDPProtocol(), local_addr=("0.0.0.0", 3478)
    )
    return protocol
