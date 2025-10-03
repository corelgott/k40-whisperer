from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List
import asyncio
import json

from app.hardware.controller import get_laser_controller

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

@router.websocket("/position")
async def websocket_position(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        controller = get_laser_controller()
        while True:
            position = await controller.get_position()
            await websocket.send_json({
                "type": "position",
                "x": position[0],
                "y": position[1],
                "timestamp": asyncio.get_event_loop().time()
            })
            await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        manager.disconnect(websocket)

@router.websocket("/status")
async def websocket_status(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        controller = get_laser_controller()
        while True:
            status = await controller.get_status()
            await websocket.send_json({
                "type": "status",
                **status,
                "timestamp": asyncio.get_event_loop().time()
            })
            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        manager.disconnect(websocket)
