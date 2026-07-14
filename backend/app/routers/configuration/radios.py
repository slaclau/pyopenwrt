import uuid

from fastapi import APIRouter, HTTPException, Response, status
from pydantic import ValidationError, model_validator
from sqlalchemy.exc import IntegrityError
from sqlmodel import JSON, Column, Field, Relationship, SQLModel

from ...dependencies import SessionDep
from .devices import Device

router = APIRouter(prefix="/configuration/radios", tags=["radios"])


class Radio(SQLModel, table=True):
    device_id: uuid.UUID = Field(primary_key=True, foreign_key="device.device_id")
    radio_id: str = Field(primary_key=True)
    hwmodes: list[str] = Field(sa_type=JSON)

    device: Device = Relationship(back_populates="radios")


@router.get("/")
def get_all_radios(session: SessionDep) -> list[Radio]:
    return session.query(Radio).all()


@router.get("/{radio_id}")
def get_radio(radio_id, session: SessionDep) -> Radio:
    radio = session.get(Radio, radio_id)
    if not radio:
        raise HTTPException(404, f"No radio with id {radio_id} found")
    return radio


@router.put("/{radio_id}")
def update_radio(radio_id: int, radio: Radio, session: SessionDep) -> Radio:
    assert radio.radio_id == radio_id
    original = session.get(Radio, radio_id)
    session.delete(original)

    return create_radio(radio, session)


@router.post(
    "/", status_code=status.HTTP_201_CREATED, responses={status.HTTP_409_CONFLICT: {}}
)
def create_radio(radio: Radio, session: SessionDep) -> Radio:
    try:
        Radio.validate(radio)
    except ValidationError as e:
        raise HTTPException(422, e.errors())
    try:
        session.add(radio)
        session.commit()
        session.refresh(radio)
        return radio
    except IntegrityError:
        raise HTTPException(409, f"Radio with id {radio.radio_id} already exists")
