import uuid
from enum import Enum

from fastapi import APIRouter, HTTPException, Response, status
from pydantic import ValidationError, model_validator
from sqlalchemy.exc import IntegrityError
from sqlmodel import JSON, Column, Field, Relationship, SQLModel

from ...dependencies import SessionDep
from .devices import Device

router = APIRouter(prefix="/configuration/ports", tags=["ports"])


class PortRole(str, Enum):
    LAN = "lan"
    WAN = "wan"


class Port(SQLModel, table=True):
    device_id: uuid.UUID = Field(primary_key=True, foreign_key="device.device_id")
    port_id: str = Field(primary_key=True)
    role: PortRole = Field()

    device: Device = Relationship(back_populates="ports")


def validate_port(port: Port, session) -> bool:
    device = session.get(Device, port.device_id)
    if port.role == PortRole.WAN:
        return "router" in device.roles
    return True


@router.get("/")
def get_all_ports(session: SessionDep) -> list[Port]:
    return session.query(Port).all()


@router.get("/{port_id}")
def get_port(port_id, session: SessionDep) -> Port:
    port = session.get(Port, port_id)
    if not port:
        raise HTTPException(404, f"No port with id {port_id} found")
    return port


@router.put("/{port_id}")
def update_port(port_id: int, port: Port, session: SessionDep) -> Port:
    assert port.port_id == port_id
    original = session.get(Port, port_id)
    session.delete(original)

    return create_port(port, session)


@router.post(
    "/", status_code=status.HTTP_201_CREATED, responses={status.HTTP_409_CONFLICT: {}}
)
def create_port(port: Port, session: SessionDep) -> Port:
    try:
        Port.validate(port)
    except ValidationError as e:
        raise HTTPException(422, e.errors())
    if not validate_port(port, session):
        raise HTTPException(422)
    try:
        session.add(port)
        session.commit()
        session.refresh(port)
        return port
    except IntegrityError:
        raise HTTPException(409, f"Port with id {port.port_id} already exists")
