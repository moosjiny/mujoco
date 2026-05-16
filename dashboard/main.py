import asyncio
import json
import os
from contextlib import asynccontextmanager
from typing import List

import httpx
from fastapi import FastAPI, WebSocket, Request
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

NTFY_BASE        = os.environ.get("NTFY_BASE", "")
MUJOCO_TOPIC_SIM = os.environ.get("MUJOCO_TOPIC_SIM", "")
NTFY_TOKEN       = os.environ.get("NTFY_TOKEN", "")  # Bearer 토큰 (필요 시)

# 3개 로봇 전체 상태
robot_state = {
    # 양팔 OpenArm (sim_dual_arm.py POST /update 와 NTFY 양쪽으로 채워짐)
    "left":  {"joints": [0.0]*7, "torque": [0.0]*7, "gripper": 0.0},
    "right": {"joints": [0.0]*7, "torque": [0.0]*7, "gripper": 0.0},
    # OMX-F 팔로워 (NTFY 수신)
    "omxf":  {"joints": [0.0]*5, "gripper": [0.0, 0.0]},
    # Vic Pinky (NTFY 수신)
    "pinky": {"xpos": [0.0, 0.0, 0.0], "wheels": [0.0, 0.0]},
    # 메타
    "status":  "WAITING",
    "ntfy_ok": False,
    "ntfy_ts": None,
}


def _apply_ntfy_state(state: dict) -> None:
    """NTFY에서 받은 sim 상태를 robot_state에 반영."""
    # bimanual.qpos layout: left arm(7) + left fingers(2) + right arm(7) + right fingers(2)
    bi = state.get("bimanual", {})
    if bi:
        qpos = bi.get("qpos", [])
        if len(qpos) >= 18:
            robot_state["left"]["joints"]  = list(qpos[0:7])
            robot_state["left"]["gripper"] = qpos[7]
            robot_state["right"]["joints"] = list(qpos[9:16])
            robot_state["right"]["gripper"] = qpos[16]

    # omxf.qpos layout: joints 1-5 + gripper 1-2
    omxf = state.get("omxf", {})
    if omxf:
        qpos = omxf.get("qpos", [])
        if len(qpos) >= 7:
            robot_state["omxf"]["joints"]  = list(qpos[0:5])
            robot_state["omxf"]["gripper"] = list(qpos[5:7])

    # pinky: xpos (world), wheel_qpos (cumulative angle)
    pinky = state.get("pinky", {})
    if pinky:
        robot_state["pinky"]["xpos"]   = list(pinky.get("xpos") or [0.0, 0.0, 0.0])
        robot_state["pinky"]["wheels"] = list(pinky.get("wheel_qpos", [0.0, 0.0]))

    robot_state["ntfy_ts"] = state.get("ts")
    robot_state["ntfy_ok"] = True
    robot_state["status"]  = "NTFY_LIVE"


async def ntfy_subscriber() -> None:
    """NTFY NdJSON 스트림을 구독해 robot_state를 갱신. 연결 실패 시 지수 백오프로 재시도."""
    if not (NTFY_BASE and MUJOCO_TOPIC_SIM):
        return  # 환경변수 미설정 → no-op

    url = f"{NTFY_BASE}/{MUJOCO_TOPIC_SIM}/json"
    headers = {}
    if NTFY_TOKEN:
        headers["Authorization"] = f"Bearer {NTFY_TOKEN}"

    delay = 2.0
    while True:
        try:
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream("GET", url, headers=headers) as resp:
                    resp.raise_for_status()
                    async for line in resp.aiter_lines():
                        if not line:
                            continue
                        try:
                            event = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        if event.get("event") != "message":
                            continue
                        try:
                            sim_state = json.loads(event["message"])
                        except (json.JSONDecodeError, KeyError, TypeError):
                            continue
                        _apply_ntfy_state(sim_state)
                        delay = 2.0  # 성공 시 delay 초기화
        except asyncio.CancelledError:
            return
        except Exception:
            robot_state["ntfy_ok"] = False
            await asyncio.sleep(delay)
            delay = min(delay * 2, 30.0)


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(ntfy_subscriber())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(lifespan=lifespan)


# --- 기존 POST /update (sim_dual_arm.py 로컬 fallback 유지) ---

class SideState(BaseModel):
    joints: List[float]
    torque: List[float]
    gripper: float

class RobotUpdate(BaseModel):
    left: SideState
    right: SideState
    status: str

@app.post("/update")
async def update_state(data: RobotUpdate):
    robot_state["left"]   = data.left.model_dump()
    robot_state["right"]  = data.right.model_dump()
    robot_state["status"] = data.status
    return {"status": "ok"}


# --- 템플릿 & WebSocket ---

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
            await asyncio.sleep(0.05)  # 20 Hz
    except Exception:
        pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
