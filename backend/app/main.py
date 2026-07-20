import asyncio
from contextlib import asynccontextmanager
import logging
import pathlib
import tarfile

from fastapi import FastAPI


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
from .site_manager import send_site_manager_heartbeat
from .stun import setup_stun_server

logger = logging.getLogger(f"uvicorn.{__name__}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    asyncio.create_task(send_site_manager_heartbeat())
    asyncio.create_task(setup_stun_server())
    asyncio.create_task(create_device_file_archive())
    yield


app = FastAPI(lifespan=lifespan)


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


async def create_device_file_archive():
    logger.info("creating device file archive")
    with tarfile.open(
        pathlib.Path(__file__).parent / "routers" / "configuration" / "informd.tar.gz",
        "w:gz",
    ) as tar:
        tar.add(
            pathlib.Path(__file__).parent.parent.parent / "device_files", arcname="/"
        )
