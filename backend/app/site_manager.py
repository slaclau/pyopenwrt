import asyncio
import json
import logging
import time

import httpx

import aiortc
import websockets

SITE_MANAGER_WS_URI = "ws://localhost:8001/controller/ws"  # Target external endpoint
SITE_MANAGER_ICE_SERVERS_URI = (
    "http://localhost:8001/ice-servers"  # Target external endpoint
)

SITE_ID = "test-site"

logger = logging.getLogger(f"uvicorn.{__name__}")


async def manage_site_manager_connection():
    try:
        while True:
            try:
                async with websockets.connect(
                    SITE_MANAGER_WS_URI, close_timeout=20
                ) as websocket:
                    logger.info(
                        f"connected to site-manager ws at {websocket.remote_address}"
                    )
                    await asyncio.gather(send_heartbeat(websocket), listen(websocket))

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
                "site-id": SITE_ID,
                "time": time.time(),
            }
        )
        await websocket.send(message)
        logger.info(f"sent {message} to site manager")
        await asyncio.sleep(10)


async def listen(websocket: websockets.ClientConnection):
    while True:
        message = json.loads(await websocket.recv())

        match message["type"]:
            case "command":
                match message["command"]:
                    case "connect":
                        async with httpx.AsyncClient() as client:
                            response = await client.get(SITE_MANAGER_ICE_SERVERS_URI)
                            servers = response.json()
                        pc = aiortc.RTCPeerConnection(
                            aiortc.RTCConfiguration(
                                iceServers=[
                                    aiortc.RTCIceServer(**server) for server in servers
                                ]
                            )
                        )

                        @pc.on("iceconnectionstatechange")
                        def on_ice_connection_state_change():
                            match pc.iceConnectionState:
                                case "checking":
                                    logger.debug("Checking ICE candidates")
                                case "completed":
                                    logger.debug("Finished checking ICE candidates")
                                case other:
                                    logger.debug(f"ICE connection state is {other}")

                        @pc.on("icegatheringstatechange")
                        def on_ice_gathering_state_change():
                            match pc.iceGatheringState:
                                case "gathering":
                                    logger.debug("Gathering ICE candidates")
                                case "complete":
                                    logger.debug("Finished gathering ICE candidates")
                                case other:
                                    logger.debug(f"ICE gathering state is {other}")

                        @pc.on("datachannel")
                        def on_data_channel(channel: aiortc.RTCDataChannel):
                            logger.info(f"data channel opened")

                            @channel.on("message")
                            def on_message(message):
                                logger.info(f"got '{message}' from browser")
                                channel.send(f"hello back")

                    case _:
                        logger.warning(f"got unknown command {message["command"]}")

            case "offer":
                offer = aiortc.RTCSessionDescription(**message["offer"])
                logger.info("Received WebRTC offer")
                await pc.setRemoteDescription(offer)

                answer = await pc.createAnswer()

                await pc.setLocalDescription(answer)
                while pc.iceGatheringState != "complete":
                    await asyncio.sleep(0.01)
                await websocket.send(
                    json.dumps(
                        {
                            "type": "answer",
                            "site-id": SITE_ID,
                            "answer": pc.localDescription.__dict__,
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

                await pc.addIceCandidate(rtc_candidate)

            case _:
                logger.warning(f"got unknown ws type {message["type"]}")
