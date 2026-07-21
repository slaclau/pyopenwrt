import asyncio
import json
import logging

import aiortc
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()

logger = logging.getLogger(f"uvicorn.{__name__}")

sites: dict[str, WebSocket] = {}
clients: dict[str, WebSocket] = {}


@app.websocket("/controller/ws")
async def controller_websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info(f"ws connection from controller {websocket.client}")
    try:
        while True:
            data = await websocket.receive_json()
            site_id = data["site-id"]
            sites[site_id] = websocket
            match data["type"]:
                case "answer":
                    await clients[site_id].send_json(data)
                    logger.info("forwarded answer")
                case "heartbeat":
                    logger.info(f"got heartbeat from {site_id}")
                case _:
                    logger.warning(f"got unknown ws type {data["type"]}")
    except WebSocketDisconnect:
        logger.info(f"controller {websocket.client} disconnected")
        sites.pop(site_id)


@app.get("/ice-servers")
def get_ice_servers():
    return [
        {
            "urls": "stun:stun.relay.metered.ca:80",
        },
        {
            "urls": "turn:global.relay.metered.ca:80",
            "username": "d87da67fe0fe83c87d7f00ab",
            "credential": "E2B6csPO3iJL2ocH",
        },
        {
            "urls": "turn:global.relay.metered.ca:80?transport=tcp",
            "username": "d87da67fe0fe83c87d7f00ab",
            "credential": "E2B6csPO3iJL2ocH",
        },
        {
            "urls": "turn:global.relay.metered.ca:443",
            "username": "d87da67fe0fe83c87d7f00ab",
            "credential": "E2B6csPO3iJL2ocH",
        },
        {
            "urls": "turns:global.relay.metered.ca:443?transport=tcp",
            "username": "d87da67fe0fe83c87d7f00ab",
            "credential": "E2B6csPO3iJL2ocH",
        },
    ]


@app.websocket("/ws")
async def client_websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info(f"ws connection from client {websocket.client}")
    try:
        while True:
            data = await websocket.receive_json()
            match data["type"]:
                case "command":
                    match data["command"]:
                        case "connect":
                            site_id = "test-site"
                            clients[site_id] = websocket
                            await sites[site_id].send_json(
                                {"type": "command", "command": "connect"}
                            )

                        case _:
                            logger.warning(f"got unknown command {data["command"]}")
                case "offer":
                    await sites[site_id].send_json(data)
                    logger.info(f"forwarded offer to {site_id}")
                case "ice-candidate":
                    await sites[site_id].send_json(data)
                    logger.info(f"forwarded candidate to {site_id}")
                case _:
                    logger.warning(f"got unknown ws type {data["type"]}")
    except WebSocketDisconnect:
        logger.info(f"client {websocket.client} disconnected")
