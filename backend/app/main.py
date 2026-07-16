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
import json
import time
import websockets

EXTERNAL_WS_URI = "ws://localhost:8001/ws"  # Target external endpoint

async def maintain_external_connection():
    try:
        # Keep-alive reconnection loop if the external endpoint drops
        while True:
            try:
                async with websockets.connect(EXTERNAL_WS_URI) as websocket:
                    print(f"Connected to external WebSocket server at {EXTERNAL_WS_URI}")
                    
                    while True:
                        await asyncio.sleep(10)  # Periodic interval
                        message = json.dumps({"type": "heartbeat", "time": time.time()})
                        await websocket.send(message)
                        
            except (websockets.ConnectionClosed, OSError) as e:
                print(f"Connection lost ({e}). Retrying in 5 seconds...")
                await asyncio.sleep(5)
    except asyncio.CancelledError:
        print("External connection client task terminated.")

@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    asyncio.create_task(maintain_external_connection())
