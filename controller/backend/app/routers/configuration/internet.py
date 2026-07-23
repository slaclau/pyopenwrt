import uuid
from ipaddress import IPv4Address, IPv4Network

from fastapi import APIRouter, HTTPException, Response, status
from pydantic import ValidationError, computed_field, model_validator
from sqlalchemy.exc import IntegrityError
from sqlmodel import JSON, Column, Field, SQLModel, Relationship

from .devices import Device
from .ports import Port, PortRole
from ...dependencies import SessionDep

router = APIRouter(prefix="/configuration/internets", tags=["internets"])


class Internet(SQLModel, table=True):
    device_id: uuid.UUID = Field(primary_key=True, foreign_key="port.device_id")
    port_id: str = Field(primary_key=True, foreign_key="port.port_id")
    name: str = Field()

    # device: Device = Relationship(back_populates="internets")
    # port: Port = Relationship()


@router.get("/")
def get_all_internets(session: SessionDep) -> list[Internet]:
    return session.query(Internet).all()


@router.get("/{device_id}/{port_id}")
def get_internet(device_id: uuid.UUID, port_id: str, session: SessionDep) -> Internet:
    internet = session.get(Internet, (device_id, port_id))
    if not internet:
        raise HTTPException(
            404,
            f"No internet on device with id {internet.device_id} and port {internet.port_id} found",
        )
    return internet


@router.put("/{device_id}/{port_id}")
def update_internet(
    device_id: uuid.UUID, port_id: str, internet: Internet, session: SessionDep
) -> Internet:
    original = session.get(Internet, (device_id, port_id))
    session.delete(original)
    session.commit()

    return create_internet(internet, session)


@router.post(
    "/", status_code=status.HTTP_201_CREATED, responses={status.HTTP_409_CONFLICT: {}}
)
def create_internet(internet: Internet, session: SessionDep) -> Internet:
    internet = Internet.model_validate(internet)
    port = session.get(Port, (internet.device_id, internet.port_id))
    if not port:
        raise HTTPException(
            409,
            f"Port {internet.port_id} on device with id {internet.device_id} does not exist",
        )
    if port.role != PortRole.WAN:
        raise HTTPException(
            409,
            f"Port {internet.port_id} on device with id {internet.device_id} is not a WAN port",
        )
    try:
        session.add(internet)
        session.commit()
        session.refresh(internet)
        return internet
    except IntegrityError:
        raise HTTPException(
            409,
            f"Internet on device with id {internet.device_id} and port {internet.port_id} already exists",
        )
