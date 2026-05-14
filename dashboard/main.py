import asyncio
import json
import random
from fastapi import FastAPI, WebSocket, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import os
from contextlib import asynccontextmanager
from pydantic import BaseModel
from typing import List

# Global state for the robot
robot_state = {
    "left": {"joints": [0.0]*7, "torque": [0.0]*7, "gripper": 0.0},
    "right": {"joints": [0.0]*7, "torque": [0.0]*7, "gripper": 0.0},
    "status": "OPERATIONAL"
}

class SideState(BaseModel):
    joints: List[float]
    torque: List[float]
    gripper: float

class RobotUpdate(BaseModel):
    left: SideState
    right: SideState
    status: str

async def update_robot_data():
    """
    Background task to update robot state with fallback mock data.
    """
    global robot_state
    while True:
        # If no updates received recently, keep current or mock
        # For now, we'll just let the POST /update handle it.
        await asyncio.sleep(1.0)

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(update_robot_data())
    yield
    task.cancel()

app = FastAPI(lifespan=lifespan)

@app.post("/update")
async def update_state(data: RobotUpdate):
    global robot_state
    robot_state = data.model_dump()
    return {"status": "ok"}

# Setup templates
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

@app.get("/")
async def get_dashboard(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            await websocket.send_text(json.dumps(robot_state))
            await asyncio.sleep(0.05)
    except Exception as e:
        pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
