import asyncio
import json
import logging
import time

import websockets

SITE_MANAGER_WS_URI = "ws://localhost:8001/ws"  # Target external endpoint


logger = logging.getLogger(f"uvicorn.{__name__}")


async def send_site_manager_heartbeat():
    try:
        while True:
            try:
                async with websockets.connect(
                    SITE_MANAGER_WS_URI, close_timeout=20
                ) as websocket:
                    logger.info(
                        f"connected to site-manager ws at {websocket.remote_address}"
                    )

                    while True:
                        message = json.dumps({"type": "heartbeat", "time": time.time()})
                        await websocket.send(message)
                        logger.info(f"sent {message} to site manager")
                        await asyncio.sleep(10)

            except (websockets.ConnectionClosed, OSError) as e:
                logger.warning(
                    f"lost connection to site-manager ({e}) - retrying in 5 seconds..."
                )
                await asyncio.sleep(5)
    except asyncio.CancelledError:
        logger.warning("site-manager heartbeat terminated")
