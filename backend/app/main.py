from fastapi import FastAPI
from fastapi import FastAPI


from .site_manager import send_site_manager_heartbeat
from .stun import setup_stun_server

from .dependencies import create_db_and_tables
from .logging import register_log_filter
from .routers.configuration import (
    devices,
    networks,
    ports,
    provisioning,
    wireless,
    internet,
)
from .routers.control import inform
from .routers.status import status
from .routers import netify

app = FastAPI()
register_log_filter()

app.frontend("/", directory="dist", fallback="index.html", check_dir=False)
app.include_router(devices.router)
app.include_router(provisioning.router)
app.include_router(networks.router)
app.include_router(wireless.router)
app.include_router(ports.router)
app.include_router(inform.router)
app.include_router(status.router)
app.include_router(internet.router)
app.include_router(netify.router)

import asyncio


@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    asyncio.create_task(send_site_manager_heartbeat())
    asyncio.create_task(setup_stun_server())
