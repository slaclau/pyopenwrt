from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.datastructures import Address

from .dependencies import create_db_and_tables
from .users import users
from .sites import sites
from .webrtc import webrtc


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(users)
app.include_router(sites)
app.include_router(webrtc)

logger = logging.getLogger(f"uvicorn.{__name__}")


# TODO: #1 Add db backend
# TODO: #3 Add users, potentially as oauth provider to controller
