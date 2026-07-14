from fastapi import FastAPI
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .dependencies import create_db_and_tables
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
app.frontend("/", directory="dist", fallback="index.html")
app.include_router(devices.router)
app.include_router(provisioning.router)
app.include_router(networks.router)
app.include_router(wireless.router)
app.include_router(ports.router)
app.include_router(inform.router)
app.include_router(status.router)
app.include_router(internet.router)
app.include_router(netify.router)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()
