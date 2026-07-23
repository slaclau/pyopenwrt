import logging
from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from fastapi.datastructures import Address
from sqlmodel import Field, Relationship, SQLModel, select

from .dependencies import SessionDep, get_session
from .links import SiteAccessRelationship
from .users import UserInDb, User, get_current_active_user, get_current_user
from .webrtc import client_websockets, site_websockets

logger = logging.getLogger(f"uvicorn.{__name__}")


class Site(SQLModel, table=True):
    site_id: uuid.UUID = Field(primary_key=True)
    name: str
    users: list[UserInDb] = Relationship(link_model=SiteAccessRelationship)


sites = APIRouter(prefix="/sites")


@sites.websocket("/ws")
async def controller_websocket_endpoint(websocket: WebSocket, session: SessionDep):
    await websocket.accept()
    logger.info(f"ws connection from site at {websocket.client}")
    try:
        while True:
            data = await websocket.receive_json()
            site_id = data["site_id"]
            site_websockets[site_id] = websocket
            match data["type"]:
                case "answer":
                    client = Address(host=data["client"][0], port=data["client"][1])
                    await client_websockets[client].send_json(data)
                    logger.info(f"forwarded answer to {client} from {site_id}")
                case "heartbeat":
                    logger.info(f"got heartbeat from {site_id}")
                    site = Site(
                        site_id=uuid.UUID(hex=data["site_id"]), name=data["name"]
                    )
                    session.merge(site)
                    session.commit()
                    logger.info(site)
                case _:
                    logger.warning(f"got unknown ws type {data["type"]}")
    except WebSocketDisconnect:
        logger.info(f"controller {websocket.client} disconnected")
        site_websockets.pop(site_id)


@sites.get("/")
def get_all_my_sites(
    session: SessionDep, user: Annotated[UserInDb, Depends(get_current_active_user)]
) -> list[Site]:
    return [
        site for site in session.exec(select(Site).where(Site.users.contains(user)))  # type: ignore[attr-defined]
    ]
