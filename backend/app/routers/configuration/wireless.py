from enum import Enum

from fastapi import APIRouter, HTTPException, Response, status
from pydantic import ValidationError, computed_field, model_validator
from sqlalchemy.exc import IntegrityError
from sqlmodel import JSON, Column, Field, SQLModel

from ...dependencies import SessionDep

router = APIRouter(prefix="/configuration/wireless", tags=["wireless"])

class WirelessEncryption(str, Enum):
    OPEN = "open"
    WPA2_PERSONAL = "wpa2_personal"

class Wireless(SQLModel, table=True):
    wireless_id: str = Field(primary_key=True)
    network_id: str = Field()
    ssid: str = Field()
    encryption: WirelessEncryption | None = Field()
    key: str | None = Field()
    
@router.get("/")
def get_all_wireless_networks(session: SessionDep) -> list[Wireless]:
    return session.query(Wireless).all()

@router.get("/{wireless_id}")
def get_wireless_network(wireless_id, session: SessionDep) -> Wireless:
    wireless = session.get(Wireless, wireless_id)
    if not wireless:
        raise HTTPException(404, f"No wireless network with id {network_id} found")
    return wireless

@router.put("/{wireless_id}")
def update_wireless_network(wireless_id: str, wireless: Wireless, session: SessionDep) -> Wireless:
    assert wireless.wireless_id == wireless_id
    original = session.get(Wireless, wireless_id)
    session.delete(original)
    session.commit()
    
    return create_wireless_network(wireless, session)

@router.post("/", status_code=status.HTTP_201_CREATED, responses={status.HTTP_409_CONFLICT: {}})
def create_wireless_network(wireless: Wireless, session: SessionDep) -> Wireless:
    try:
        Wireless.validate(wireless)
    except ValidationError as e:
        raise HTTPException(422, e.errors())

    try:
        session.add(wireless)
        session.commit()
        session.refresh(wireless)
        return wireless
    except IntegrityError:
        raise HTTPException(409, f"Wireless network with id {wireless.wireless_id} already exists")
