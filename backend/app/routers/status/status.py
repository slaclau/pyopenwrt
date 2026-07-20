import datetime
import time
import typing
import uuid
from ipaddress import IPv4Address

from fastapi import APIRouter
from pydantic import BaseModel, computed_field
from pydantic_extra_types.mac_address import MacAddress
from sqlmodel import Field, Relationship, SQLModel

from ..configuration.networks import (
    get_all_networks,
    IPv4AddressType,
    NetworkWithDevices,
)
from ...dependencies import SessionDep
from ..configuration.devices import Device, get_all_devices
from ..configuration.networks import Network

router = APIRouter(prefix="/status", tags=["status"])


class DeviceStatusBase(SQLModel):
    device_id: uuid.UUID = Field(primary_key=True, foreign_key="device.device_id")
    last_inform: float | None = Field(default=None)
    last_ip: IPv4Address | None = Field(default=None)
    boot_time: datetime.datetime | None = Field(default=None)
    nat_ip: IPv4Address | None = Field(default=None)
    nat_port: int | None = Field(default=None)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def time_since_inform(self) -> float | None:
        if not self.last_inform:
            return None
        return time.time() - self.last_inform

    @computed_field  # type: ignore[prop-decorator]
    @property
    def up(self) -> bool:
        t = self.time_since_inform
        if t is None:
            return False
        return t < 30

    @computed_field  # type: ignore[prop-decorator]
    @property
    def uptime(self) -> float | None:
        if self.up and self.boot_time is not None:
            return time.time() - self.boot_time.timestamp()
        return None


class DeviceStatus(DeviceStatusBase, table=True):
    device: Device = Relationship(back_populates="status")


class DeviceStatusWithDevice(DeviceStatusBase):
    device: Device


class NetworkStatus(BaseModel):
    network: NetworkWithDevices = Field()
    dhcp_leases: list["DHCPLease"] = Field(default=[])


class Status(BaseModel):
    device_status: list[DeviceStatusWithDevice] = Field(default=[])
    network_status: list[NetworkStatus] = Field(default=[])


class DHCPLeaseBase(SQLModel):
    expires: int
    hostname: str | None = None
    macaddr: MacAddress = Field(primary_key=True)
    ipaddr: IPv4Address = Field(sa_type=IPv4AddressType)
    duid: str | None = None


class DHCPLease(DHCPLeaseBase, table=True):
    device_id: uuid.UUID = Field(primary_key=True, foreign_key="devicestatus.device_id")


@router.get("")
def get_status(session: SessionDep) -> Status:
    rtn = {}
    device_status = []
    for device in get_all_devices(session):
        status = session.get(DeviceStatus, device.device_id)
        if not status:
            status = DeviceStatusWithDevice(device_id=device.device_id, device=device)
        device_status.append(status)
    rtn["device_status"] = device_status
    network_status = []
    leases = session.query(DHCPLease).where(DHCPLease.expires >= time.time()).all()
    for network in get_all_networks(session):
        network_status.append(
            {
                "network": network,
                "dhcp_leases": [
                    lease for lease in leases if lease.ipaddr in network.network.hosts()
                ],
            }
        )
    rtn["network_status"] = network_status
    return rtn
