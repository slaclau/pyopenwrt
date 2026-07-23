import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.datastructures import Address

logger = logging.getLogger(f"uvicorn.{__name__}")

webrtc = APIRouter(prefix="")

client_websockets: dict[Address, WebSocket] = {}
site_websockets: dict[str, WebSocket] = {}


@webrtc.get("/ice-servers")
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


@webrtc.websocket("/ws")
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
                            site_id = data["site_id"]
                            assert websocket.client
                            client_websockets[websocket.client] = websocket
                            if site_id not in site_websockets:
                                await websocket.send_json(
                                    {"type": "error", "error": f"no site {site_id}"}
                                )
                            else:
                                await websocket.send_json(
                                    {"type": "connected", "site-id": site_id}
                                )
                                await site_websockets[site_id].send_json(
                                    {
                                        "type": "command",
                                        "command": "connect",
                                        "client": websocket.client,
                                    }
                                )

                        case _:
                            logger.warning(f"got unknown command {data["command"]}")
                case "offer":
                    data["client"] = websocket.client
                    await site_websockets[site_id].send_json(data)
                    logger.info(f"forwarded offer to {site_id} from {websocket.client}")
                case "ice-candidate":
                    data["client"] = websocket.client
                    await site_websockets[site_id].send_json(data)
                    logger.info(
                        f"forwarded candidate to {site_id} from {websocket.client}"
                    )
                case _:
                    logger.warning(f"got unknown ws type {data["type"]}")
    except WebSocketDisconnect:
        logger.info(f"client {websocket.client} disconnected")
