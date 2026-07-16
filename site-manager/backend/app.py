import json
import logging

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()

logger = logging.getLogger(f"uvicorn.{__name__}")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info(f"ws connection from {websocket.client}")
    try:
        while True:
            data = await websocket.receive_json()
            logger.info(f"received {data} from {websocket.client}")
    except WebSocketDisconnect:
        logger.info(f"{websocket.client} disconnected")
