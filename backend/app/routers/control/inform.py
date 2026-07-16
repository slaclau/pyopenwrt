import datetime
import pathlib
import time
import typing
import uuid
from enum import Enum
from ipaddress import IPv4Address
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, status as status_codes
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pydantic_extra_types.mac_address import MacAddress
from sqlmodel import SQLModel, Field, Relationship

from ..configuration.ports import PortRole, Port
from ..configuration.radios import Radio
from ...dependencies import SessionDep
from ..configuration.devices import Device, AddressProto, DeviceRole
from ..status.status import DHCPLeaseBase, DHCPLease, DeviceStatus

router = APIRouter(prefix="/control", tags=["control"])


class InterfaceStats(BaseModel):
    name: str


class AssoclistItem(BaseModel):
    mac: MacAddress


class Iwinfo(BaseModel):
    device: str
    assoclist: list[AssoclistItem]


class InformPayload(BaseModel):
    device_id: Optional[uuid.UUID] = None
    ip: IPv4Address
    boot_time: datetime.datetime
    iwinfo: list[Iwinfo] = Field(default=[])
    interface_stats: Optional[dict[str, InterfaceStats]] = Field(default={})
    model: str | None = None
    ports: dict[str, str] = Field()
    dhcp_leases: list[DHCPLeaseBase] = Field()
    radios: dict[str, dict] = Field()


class DeviceCommand(Enum):
    NOOP = "noop"
    ADOPT = "adopt"
    PROVISION = "provision"
    REBOOT = "reboot"
    FORGET = "forget"
    UPDATE_INFORM = "update-inform"
    LOCATE = "locate"
    STOP_LOCATE = "stop-locate"


class Command(SQLModel, table=True):
    device_id: uuid.UUID = Field(primary_key=True)
    command: DeviceCommand = Field()


class InformResponse(Command):
    pass


@router.post("/reboot/{device_id}")
def reboot(device_id: uuid.UUID, session: SessionDep):
    command = Command(device_id=device_id, command=DeviceCommand.REBOOT)
    session.add(command)
    status = session.get(DeviceStatus, device_id)
    if status:
        status.last_inform = None
    else:
        raise HTTPException(status_code=status_codes.HTTP_500_INTERNAL_SERVER_ERROR)
    session.commit()


@router.post("/locate/{device_id}")
def locate(device_id: uuid.UUID, session: SessionDep):
    command = Command(device_id=device_id, command=DeviceCommand.LOCATE)
    session.add(command)
    session.commit()


@router.post("/stop-locate/{device_id}")
def stop_locate(device_id: uuid.UUID, session: SessionDep):
    command = Command(device_id=device_id, command=DeviceCommand.STOP_LOCATE)
    session.add(command)
    session.commit()


@router.post("/adopt/{device_id}")
def adopt(device_id: uuid.UUID, session: SessionDep):
    command = Command(device_id=device_id, command=DeviceCommand.ADOPT)
    session.add(command)
    device = session.get(Device, device_id)
    if device:
        device.adopted = True
    else:
        raise HTTPException(status_code=status_codes.HTTP_500_INTERNAL_SERVER_ERROR)
    session.commit()


@router.post("/provision")
def provision_all(session: SessionDep):
    devices = session.query(Device).all()
    for device in devices:
        if device.adopted:
            provision(device.device_id, session)


@router.post("/update-inform")
def update_inform(session: SessionDep):
    devices = session.query(Device).all()
    for device in devices:
        command = Command(
            device_id=device.device_id, command=DeviceCommand.UPDATE_INFORM
        )
        session.add(command)
    session.commit()


@router.post("/provision/{device_id}")
def provision(device_id: uuid.UUID, session: SessionDep):
    command = Command(device_id=device_id, command=DeviceCommand.PROVISION)
    session.add(command)
    session.commit()


@router.post("/inform")
def inform(
    payload: InformPayload, request: Request, session: SessionDep
) -> InformResponse:
    rtn: InformResponse = InformResponse()
    if payload.device_id is None:
        device_id = uuid.uuid4()
    else:
        device_id = payload.device_id

    device = session.get(Device, device_id)
    if device is None:
        device = Device(
            device_id=device_id,
            hostname="OpenWrt",
            roles=[],
            address_proto=AddressProto.DHCP,
            adopted=False,
        )
        session.add(device)
    for port, role in payload.ports.items():
        if not session.get(Port, (device.device_id, port)):
            try:
                role = PortRole(role)
            except ValueError:
                role = PortRole.LAN
            session.add(Port(device_id=device.device_id, port_id=port, role=role))
    for radio, values in payload.radios.items():
        if not session.get(Radio, (device.device_id, radio)):
            session.add(
                Radio(
                    device_id=device.device_id,
                    radio_id=radio,
                    hwmodes=values["iwinfo"]["hwmodes"],
                )
            )
    if payload.radios and not device.adopted and not DeviceRole.AP in device.roles:
        device.roles = device.roles + [DeviceRole.AP]
    time_now = time.time()
    for lease in payload.dhcp_leases:
        lease_record = DHCPLease()
        lease_record.device_id = device.device_id
        for k, v in lease.model_dump().items():
            lease_record.__setattr__(k, v)
        lease_record.expires += int(time_now)
        session.merge(lease_record)
    if payload.model:
        device.model = payload.model

    if command := session.get(Command, device.device_id):
        rtn = InformResponse(device_id=command.device_id, command=command.command)
        session.delete(command)
    else:
        rtn = InformResponse(device_id=device_id, command=DeviceCommand.NOOP)

    status = DeviceStatus(
        device_id=device.device_id,
        last_inform=time.time(),
        last_ip=str(payload.ip),
        boot_time=payload.boot_time,
    )
    if rtn.command == DeviceCommand.REBOOT:
        status.last_inform = None
    session.merge(status)
    session.commit()
    return rtn


@router.get("/script/{name}")
def get_script(name: str):
    return FileResponse(pathlib.Path(__file__).parent / "script" / name)
