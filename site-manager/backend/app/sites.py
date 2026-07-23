import logging
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.datastructures import Address
from sqlmodel import Field, Relationship, SQLModel, select

from .dependencies import SessionDep, get_session
from .links import SiteAccessRelationship
from .users import UserInDb, User
from .webrtc import client_websockets, site_websockets

logger = logging.getLogger(f"uvicorn.{__name__}")


class Site(SQLModel, table=True):
    site_id: uuid.UUID = Field(primary_key=True)
    users: list[UserInDb] = Relationship(link_model=SiteAccessRelationship)


sites = APIRouter(prefix="/sites")


@sites.websocket("/ws")
async def controller_websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info(f"ws connection from controller {websocket.client}")
    try:
        while True:
            data = await websocket.receive_json()
            site_id = data["site-id"]
            site_websockets[site_id] = websocket
            match data["type"]:
                case "answer":
                    client = Address(host=data["client"][0], port=data["client"][1])
                    await client_websockets[client].send_json(data)
                    logger.info(f"forwarded answer to {client} from {site_id}")
                case "heartbeat":
                    logger.info(f"got heartbeat from {site_id}")
                case _:
                    logger.warning(f"got unknown ws type {data["type"]}")
    except WebSocketDisconnect:
        logger.info(f"controller {websocket.client} disconnected")
        site_websockets.pop(site_id)


@sites.get("/")
def get_all_sites(session: SessionDep) -> list[Site]:
    return [site for site in session.exec(select(Site))]


print(get_all_sites(session=get_session().__next__()))
