import asyncio
import json
import logging

import aiortc
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()

logger = logging.getLogger(f"uvicorn.{__name__}")

sites: dict[str, WebSocket] = {}


@app.websocket("/controller/ws")
async def controller_websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info(f"ws connection from controller {websocket.client}")
    try:
        while True:
            data = await websocket.receive_json()
            site_id = data["site-id"]
            sites[site_id] = websocket
            logger.info(f"received {data} from {websocket.client}")
    except WebSocketDisconnect:
        logger.info(f"controller {websocket.client} disconnected")
        sites.pop(site_id)


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
                            servers = [
                                {
                                    "urls": "stun:stun.relay.metered.ca:80",
                                },
                                {
                                    "urls": "turn:global.relay.metered.ca:80",
                                    "username": "d87da67fe0fe83c87d7f00ab",
                                    "credential": "E2B6csPO3iJL2ocH",
                                },
                                # {
                                #     "urls": "turn:global.relay.metered.ca:80?transport=tcp",
                                #     "username": "d87da67fe0fe83c87d7f00ab",
                                #     "credential": "E2B6csPO3iJL2ocH",
                                # },
                                # {
                                #     "urls": "turn:global.relay.metered.ca:443",
                                #     "username": "d87da67fe0fe83c87d7f00ab",
                                #     "credential": "E2B6csPO3iJL2ocH",
                                # },
                                # {
                                #     "urls": "turns:global.relay.metered.ca:443?transport=tcp",
                                #     "username": "d87da67fe0fe83c87d7f00ab",
                                #     "credential": "E2B6csPO3iJL2ocH",
                                # },
                            ]
                            pc = aiortc.RTCPeerConnection(
                                aiortc.RTCConfiguration(
                                    iceServers=[
                                        aiortc.RTCIceServer(**server)
                                        for server in servers
                                    ]
                                )
                            )

                            @pc.on("iceconnectionstatechange")
                            def on_ice_connection_state_change():
                                logger.info(f"ice conn {pc.iceConnectionState}")

                            @pc.on("icegatheringstatechange")
                            def on_ice_gathering_state_change():
                                logger.info(f"ice gather {pc.iceGatheringState}")

                            @pc.on("connectionstate")
                            def on_connection_state_change():
                                logger.info(f"connection state {pc.connectionState}")

                            @pc.on("datachannel")
                            def on_data_channel(channel):
                                logger.info(f"data channel {channel}")

                                @channel.on("message")
                                def on_message(message):
                                    logger.info(f"got {message}")

                        case _:
                            logger.warning(f"got unknown command {data["command"]}")
                case "offer":
                    offer = aiortc.RTCSessionDescription(**data["offer"])
                    await pc.setRemoteDescription(offer)

                    answer = await pc.createAnswer()
                    print(f"{answer.sdp}")

                    await pc.setLocalDescription(answer)
                    while pc.iceGatheringState != "complete":
                        await asyncio.sleep(0.01)
                    await websocket.send_json(
                        {"type": "offer", "offer": pc.localDescription.__dict__}
                    )

                    logger.info(
                        f"received {offer} and sent {answer}, state is now {pc.connectionState}/{pc.signalingState}"
                    )
                case "ice-candidate":
                    candidate = data["ice-candidate"]
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

                    await pc.addIceCandidate(rtc_candidate)
                    logger.info(
                        f"added received candidate {rtc_candidate}, ice state is {pc.iceConnectionState}/{pc.iceGatheringState}"
                    )
                case _:
                    logger.warning(f"got unknown ws type {data["type"]}")
    except WebSocketDisconnect:
        logger.info(f"client {websocket.client} disconnected")
