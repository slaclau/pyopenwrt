import asyncio
import json
import logging
import os
import time
import uuid

from fastapi import FastAPI
import httpx

import aiortc
import websockets

SITE_MANAGER_WS_URI = "ws://localhost:8001/sites/ws"  # Target external endpoint
SITE_MANAGER_ICE_SERVERS_URI = (
    "http://localhost:8001/ice-servers"  # Target external endpoint
)

if not os.path.exists("SITE_ID"):
    with open("SITE_ID", "w") as f:
        f.write(str(uuid.uuid4()))


with open("SITE_ID") as f:
    SITE_ID = f.read()

logger = logging.getLogger(f"uvicorn.{__name__}")
access_logger = logging.getLogger(f"uvicorn.access.{__name__}")


async def manage_site_manager_connection(app: FastAPI):
    try:
        while True:
            try:
                async with websockets.connect(
                    SITE_MANAGER_WS_URI, close_timeout=20
                ) as websocket:
                    logger.info(
                        f"connected to site-manager ws at {websocket.remote_address}"
                    )
                    await asyncio.gather(
                        send_heartbeat(websocket), listen(websocket, app)
                    )

            except (websockets.ConnectionClosed, OSError) as e:
                logger.warning(
                    f"lost connection to site-manager ({e}) - retrying in 5 seconds..."
                )
                await asyncio.sleep(5)
    except asyncio.CancelledError:
        logger.warning("site-manager heartbeat terminated")


async def send_heartbeat(websocket: websockets.ClientConnection):
    while True:
        message = json.dumps(
            {
                "type": "heartbeat",
                "site_id": SITE_ID,
                "name": "Test Site",
                "time": time.time(),
            }
        )
        await websocket.send(message)
        logger.info(f"sent {message} to site manager")
        await asyncio.sleep(10)


connections: dict[tuple[str, int], aiortc.RTCPeerConnection] = {}


async def listen(websocket: websockets.ClientConnection, app: FastAPI):
    transport = httpx.ASGITransport(app=app)
    while True:
        message = json.loads(await websocket.recv())

        match message["type"]:
            case "command":
                match message["command"]:
                    case "connect":
                        logger.info(
                            f"Connection request received from {tuple(message["client"])}"
                        )
                        async with httpx.AsyncClient() as client:
                            response = await client.get(SITE_MANAGER_ICE_SERVERS_URI)
                            servers = response.json()
                        connections[tuple(message["client"])] = (
                            aiortc.RTCPeerConnection(
                                aiortc.RTCConfiguration(
                                    iceServers=[
                                        aiortc.RTCIceServer(**server)
                                        for server in servers
                                    ]
                                )
                            )
                        )

                        @connections[tuple(message["client"])].on(
                            "iceconnectionstatechange"
                        )
                        def on_ice_connection_state_change():
                            match connections[
                                tuple(message["client"])
                            ].iceConnectionState:
                                case "checking":
                                    logger.debug("Checking ICE candidates")
                                case "completed":
                                    logger.debug("Finished checking ICE candidates")
                                case other:
                                    logger.debug(f"ICE connection state is {other}")

                        @connections[tuple(message["client"])].on(
                            "icegatheringstatechange"
                        )
                        def on_ice_gathering_state_change():
                            match connections[
                                tuple(message["client"])
                            ].iceGatheringState:
                                case "gathering":
                                    logger.debug("Gathering ICE candidates")
                                case "complete":
                                    logger.debug("Finished gathering ICE candidates")
                                case other:
                                    logger.debug(f"ICE gathering state is {other}")

                        @connections[tuple(message["client"])].on("datachannel")
                        def on_data_channel(channel: aiortc.RTCDataChannel):
                            logger.info(f"data channel opened")

                            @channel.on("message")
                            async def on_message(dc_message):
                                dc_message = json.loads(dc_message)
                                match dc_message["type"]:
                                    case "request":
                                        async with httpx.AsyncClient(
                                            transport=transport
                                        ) as client:
                                            resp = await client.request(
                                                method=dc_message["method"],
                                                url="http://internal"
                                                + dc_message["path"],
                                                json=(
                                                    json.loads(dc_message["body"])
                                                    if dc_message["body"]
                                                    else None
                                                ),
                                            )
                                            access_logger.info(
                                                '%s - "%s %s HTTP/%s" %d',
                                                "WebRTC Data Channel",
                                                dc_message["method"],
                                                dc_message["path"],
                                                "WebRTC",
                                                resp.status_code,
                                            )
                                            channel.send(
                                                json.dumps(
                                                    {
                                                        "type": "response",
                                                        "id": dc_message["id"],
                                                        "body": resp.json(),
                                                        "status": resp.status_code,
                                                    }
                                                )
                                            )
                                    case _:
                                        logger.warning(
                                            f"unexpected data channel message {dc_message}"
                                        )

                    case _:
                        logger.warning(f"got unknown command {message["command"]}")

            case "offer":
                offer = aiortc.RTCSessionDescription(**message["offer"])
                logger.info("Received WebRTC offer")
                await connections[tuple(message["client"])].setRemoteDescription(offer)

                answer = await connections[tuple(message["client"])].createAnswer()

                await connections[tuple(message["client"])].setLocalDescription(answer)
                while (
                    connections[tuple(message["client"])].iceGatheringState
                    != "complete"
                ):
                    await asyncio.sleep(0.01)
                await websocket.send(
                    json.dumps(
                        {
                            "type": "answer",
                            "site_id": SITE_ID,
                            "client": tuple(message["client"]),
                            "answer": connections[
                                tuple(message["client"])
                            ].localDescription.__dict__,
                        }
                    )
                )

                logger.info(f"Sent WebRTC answer")

            case "ice-candidate":
                candidate = message["ice-candidate"]
                if not (candidate and len(candidate["candidate"].split(" ")) > 7):
                    break
                ip = candidate["candidate"].split(" ")[4]
                port = candidate["candidate"].split(" ")[5]
                protocol = candidate["candidate"].split(" ")[7]
                priority = candidate["candidate"].split(" ")[3]
                foundation = candidate["candidate"].split(" ")[0]
                component = candidate["candidate"].split(" ")[1]
                type = candidate["candidate"].split(" ")[7]
                rtc_candidate = aiortc.RTCIceCandidate(
                    ip=ip,
                    port=port,
                    protocol=protocol,
                    priority=priority,
                    foundation=foundation,
                    component=component,
                    type=type,
                    sdpMid=candidate["sdpMid"],
                    sdpMLineIndex=candidate["sdpMLineIndex"],
                )

                await connections[tuple(message["client"])].addIceCandidate(
                    rtc_candidate
                )

            case _:
                logger.warning(f"got unknown ws type {message["type"]}")
