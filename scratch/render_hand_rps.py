"""가위바위보 3자세를 각각 수렴시킨 뒤 오프스크린 렌더링해 PNG로 저장. thesis 삽화용."""
import sys
from pathlib import Path

import mujoco
import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hand_rps_config import ordered_joint_names, target_vector  # noqa: E402
from build_hand_mjcf import JOINT_LIMITS  # noqa: E402

MODEL_PATH = str(Path(__file__).resolve().parent.parent / "urdf" / "hand_rps.xml")
OUT_DIR = Path(__file__).resolve().parent.parent / "captures"
OUT_DIR.mkdir(exist_ok=True)

model = mujoco.MjModel.from_xml_path(MODEL_PATH)
data = mujoco.MjData(model)

joint_names = ordered_joint_names()
act_ids = np.array([
    mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, f"{f}_{j}_ctrl")
    for f, j in joint_names
])

renderer = mujoco.Renderer(model, height=480, width=640)

cam = mujoco.MjvCamera()
cam.lookat[:] = [0.0, 0.05, 0.14]
cam.distance = 0.32
cam.azimuth = -35
cam.elevation = -25

qpos_ids = np.array([
    model.jnt_qposadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, f"{f}_{j}")]
    for f, j in joint_names
])

for gesture in ("rock", "paper", "scissors"):
    # 정적 자세 시각화 목적 — 목표각을 직접 qpos에 대입(kinematic)해 접촉/게인 오차 없이
    # 원 스펙 그대로의 형상을 보여준다. 동역학 추종 자체는 sim_hand_rps.py에서 별도 검증함.
    # Dex5-1 실측 관절 한계를 넘는 목표값은 실제 하드웨어라면 도달 불가능하므로 클리핑하고 콘솔에 보고한다.
    mujoco.mj_resetData(model, data)
    raw_targets = dict(zip(joint_names, target_vector(gesture)))
    clipped = []
    targets = []
    for (finger, joint) in joint_names:
        val = raw_targets[(finger, joint)]
        lo, hi = JOINT_LIMITS[(finger, joint)]
        c = min(max(val, lo), hi)
        if c != val:
            clipped.append((finger, joint, val, c))
        targets.append(c)
    if clipped:
        print(f"[{gesture}] Dex5-1 한계 초과로 클리핑됨:")
        for finger, joint, orig, c in clipped:
            print(f"   {finger}.{joint}: {orig:+.3f} -> {c:+.3f} rad")
    data.qpos[qpos_ids] = targets
    mujoco.mj_forward(model, data)
    renderer.update_scene(data, camera=cam)
    img = renderer.render()
    out_path = OUT_DIR / f"hand_rps_{gesture}.png"
    Image.fromarray(img).save(out_path)
    print(f"saved {out_path} ({img.shape[1]}x{img.shape[0]})")
