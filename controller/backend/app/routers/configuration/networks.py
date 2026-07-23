import typing
import uuid
from ipaddress import IPv4Address, IPv4Network

from fastapi import APIRouter, HTTPException, status
from pydantic import ValidationError, computed_field
from sqlalchemy.exc import IntegrityError
from sqlmodel import Field, SQLModel, Relationship, AutoString

from .devices import Device
from ...dependencies import SessionDep

router = APIRouter(prefix="/configuration/networks", tags=["networks"])


class IPv4AddressType(AutoString):
    def process_bind_param(self, value, dialect) -> typing.Optional[str]:
        if value is None or value == "None":
            return None

        if isinstance(value, str):
            # Test if value is a valid IP address to avoid process result value failling
            try:
                IPv4Address(value)
            except ValueError as e:
                raise ValueError(f"{value} is not a valid IP address") from e

        return str(value)

    def process_result_value(self, value, dialect) -> typing.Optional[IPv4Address]:
        if value is None or value == "None":
            return None

        return IPv4Address(value)


class NetworkBase(SQLModel):
    network_id: str = Field(primary_key=True)
    name: str = Field()
    gateway_ip: IPv4Address = Field(sa_type=IPv4AddressType)
    subnet_mask: int = Field(ge=0, le=32)
    management: bool = Field()
    vlan_id: int = Field()
    router_id: uuid.UUID | None = Field(foreign_key="device.device_id")
    dhcp_server_id: uuid.UUID | None = Field(foreign_key="device.device_id")
    dhcp_start_ip: IPv4Address | None = Field(sa_type=IPv4AddressType)
    dhcp_end_ip: IPv4Address | None = Field(sa_type=IPv4AddressType)

    @property
    def network(self) -> IPv4Network:
        return IPv4Network(f"{self.gateway_ip}/{self.subnet_mask}", strict=False)

    @computed_field
    def broadcast_address(self) -> IPv4Address:
        return self.network.broadcast_address

    @computed_field
    def network_address(self) -> str:
        return f"{self.network.network_address}/{self.network.prefixlen}"

    @computed_field
    def dhcp_pool_size(self) -> int:
        return int(self.dhcp_end_ip) - int(self.dhcp_start_ip) + 1

    @computed_field
    def dhcp_offset(self) -> int:
        return int(self.dhcp_start_ip) - int(self.network.network_address)


class Network(NetworkBase, table=True):
    router: Device | None = Relationship(
        sa_relationship_kwargs={"foreign_keys": "Network.router_id"}
    )
    dhcp_server: Device | None = Relationship(
        sa_relationship_kwargs={"foreign_keys": "Network.dhcp_server_id"}
    )


class NetworkWithDevices(NetworkBase):
    router: Device | None
    dhcp_server: Device | None


@router.get("/")
def get_all_networks(session: SessionDep) -> list[NetworkWithDevices]:
    return session.query(Network).all()


@router.get("/{network_id}")
def get_network(network_id, session: SessionDep) -> NetworkWithDevices:
    network = session.get(Network, network_id)
    if not network:
        raise HTTPException(404, f"No network with id {network_id} found")
    return network


@router.put("/{network_id}")
def update_network(network_id: str, network: Network, session: SessionDep) -> Network:
    network = Network.model_validate(network)
    assert network.network_id == network_id
    original = session.get(Network, network_id)
    for k, v in network.model_dump().items():
        try:
            original.__setattr__(k, v)
        except AttributeError:
            pass
    session.commit()
    session.refresh(original)
    return original


@router.post(
    "/", status_code=status.HTTP_201_CREATED, responses={status.HTTP_409_CONFLICT: {}}
)
def create_network(network: Network, session: SessionDep) -> Network:
    try:
        Network.validate(network)
    except ValidationError as e:
        raise HTTPException(422, e.errors())

    try:
        session.add(network)
        session.commit()
        session.refresh(network)
        return network
    except IntegrityError:
        raise HTTPException(409, f"Network with id {network.network_id} already exists")
