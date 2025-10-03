from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from typing import Dict
from pydantic import BaseModel

from app.hardware.controller import get_laser_controller

router = APIRouter()

class MoveRequest(BaseModel):
    dx: float
    dy: float

class PositionResponse(BaseModel):
    x: float
    y: float

@router.post("/move")
async def move_laser(request: MoveRequest):
    controller = get_laser_controller()
    try:
        await controller.move(request.dx, request.dy)
        position = await controller.get_position()
        return PositionResponse(x=position[0], y=position[1])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/home")
async def home_laser():
    controller = get_laser_controller()
    try:
        await controller.home()
        position = await controller.get_position()
        return PositionResponse(x=position[0], y=position[1])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/position")
async def get_position():
    controller = get_laser_controller()
    position = await controller.get_position()
    return PositionResponse(x=position[0], y=position[1])

@router.post("/execute/{project_id}")
async def execute_project(project_id: str):
    import asyncio
    controller = get_laser_controller()
    try:
        asyncio.create_task(controller.execute_project(project_id))
        return {"status": "started", "project_id": project_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stop")
async def stop_execution():
    controller = get_laser_controller()
    await controller.stop()
    return {"status": "stopped"}

@router.get("/status")
async def get_status():
    controller = get_laser_controller()
    status = await controller.get_status()
    return status
