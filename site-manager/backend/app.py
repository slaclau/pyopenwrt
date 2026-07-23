import logging

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.datastructures import Address

app = FastAPI()

logger = logging.getLogger(f"uvicorn.{__name__}")

sites: dict[str, WebSocket] = {}
clients: dict[Address, WebSocket] = {}

# TODO: #1 Add db backend
# TODO: #3 Add users, potentially as oauth provider to controller


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
                    client = Address(host=data["client"][0], port=data["client"][1])
                    await clients[client].send_json(data)
                    logger.info(f"forwarded answer to {client} from {site_id}")
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
                            assert websocket.client
                            clients[websocket.client] = websocket
                            if site_id not in sites:
                                await websocket.send_json(
                                    {"type": "error", "error": f"no site {site_id}"}
                                )
                            else:
                                await websocket.send_json(
                                    {"type": "connected", "site-id": site_id}
                                )
                                await sites[site_id].send_json(
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
                    await sites[site_id].send_json(data)
                    logger.info(f"forwarded offer to {site_id} from {websocket.client}")
                case "ice-candidate":
                    data["client"] = websocket.client
                    await sites[site_id].send_json(data)
                    logger.info(
                        f"forwarded candidate to {site_id} from {websocket.client}"
                    )
                case _:
                    logger.warning(f"got unknown ws type {data["type"]}")
    except WebSocketDisconnect:
        logger.info(f"client {websocket.client} disconnected")
