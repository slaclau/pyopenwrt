import uuid
from enum import Enum
from ipaddress import IPv4Address
from typing import TYPE_CHECKING

from fastapi import APIRouter, HTTPException, Response, status
from pydantic import ValidationError, model_validator
from sqlalchemy.exc import IntegrityError
from sqlmodel import JSON, Column, Field, Relationship, SQLModel


from ...dependencies import SessionDep

router = APIRouter(prefix="/configuration/devices", tags=["devices"])

if TYPE_CHECKING:
    from ..status.status import DeviceStatus
    from .ports import Port
    from .internet import Internet
    from .radios import Radio


class DeviceRole(str, Enum):
    ROUTER = "router"
    AP = "ap"
    SWITCH = "switch"


class AddressProto(str, Enum):
    STATIC = "static"
    DHCP = "dhcp"


class DeviceBase(SQLModel):
    device_id: uuid.UUID = Field(primary_key=True)
    hostname: str = Field()
    roles: list[DeviceRole] = Field(sa_column=Column(JSON))
    address_proto: AddressProto = Field()
    address: IPv4Address | None = Field()
    adopted: bool = Field()
    model: str | None = Field()

    @model_validator(mode="after")
    def validate_address(self):
        match self.address_proto:
            case AddressProto.DHCP:
                if self.address is not None:
                    raise ValueError("DHCP requires that no address is provided")
            case AddressProto.STATIC:
                if self.address is None:
                    raise ValueError("An address must be provided")
        return self

    @property
    def lan_ports(self):
        return [port for port in self.ports if port.role == "lan"]

    @property
    def wan_ports(self):
        return [port for port in self.ports if port.role == "wan"]


class Device(DeviceBase, table=True):
    ports: list["Port"] = Relationship(back_populates="device")
    radios: list["Radio"] = Relationship(back_populates="device")
    status: "DeviceStatus" = Relationship(back_populates="device")
    # internets: list["Internet"] = Relationship(back_populates="device")


class DeviceWithStatus(DeviceBase):
    status: "DeviceStatus"


@router.get("/")
def get_all_devices(session: SessionDep) -> list[Device]:
    return session.query(Device).all()

@router.get("/by-role/{role}")
def get_device_by_role(role: DeviceRole, session: SessionDep):
    return [device for device in get_all_devices(session) if role in device.roles]

@router.get("/{device_id}")
def get_device(device_id: uuid.UUID, session: SessionDep) -> Device:
    device = session.get(Device, device_id)
    if not device:
        raise HTTPException(404, f"No device with id {device_id} found")
    return device


@router.put("/{device_id}")
def update_device(device_id: uuid.UUID, device: Device, session: SessionDep) -> Device:
    device = Device.model_validate(device)
    assert device.device_id == device_id
    original = session.get(Device, device_id)
    for k, v in device.model_dump().items():
        if k == "address" and v is not None:
            original.address = str(v)
        else:
            original.__setattr__(k, v)
    session.commit()
    session.refresh(original)
    return device


@router.post(
    "/", status_code=status.HTTP_201_CREATED, responses={status.HTTP_409_CONFLICT: {}}
)
def create_device(device: Device, session: SessionDep) -> Device:
    try:
        Device.validate(device)
    except ValidationError as e:
        raise HTTPException(422, e.errors())

    try:
        session.add(device)
        session.commit()
        session.refresh(device)
        return device
    except IntegrityError:
        raise HTTPException(409, f"Device with id {device.device_id} already exists")
