"""
가위바위보(Rock-Paper-Scissors) 20-DOF 손 모델 시뮬레이션.

urdf/hand_rps.xml(scratch/build_hand_mjcf.py로 생성)을 로드하고,
scratch/hand_rps_config.py의 목표 관절각으로 위치 서보 제어해 세 자세를 순환한다.

실행:
  python3 scripts/sim_hand_rps.py            # 뷰어 창(GUI) — DISPLAY 필요
  python3 scripts/sim_hand_rps.py --headless # 뷰어 없이 각 자세 도달 여부만 콘솔 출력
  python3 scripts/sim_hand_rps.py --gesture rock   # 자세 하나만 유지

MUJOCO_GL=egl 헤드리스 렌더링 환경변수는 start_all.sh 관례를 따른다.
"""
import argparse
import sys
import time
from pathlib import Path

import numpy as np
import mujoco

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scratch"))
from hand_rps_config import (  # noqa: E402
    GESTURES,
    STATE_TRANSITION_SEQUENCE,
    ordered_joint_names,
    target_vector,
)

MODEL_PATH = str(Path(__file__).resolve().parent.parent / "urdf" / "hand_rps.xml")
HOLD_SECONDS = 2.0


def build_index_maps(model):
    joint_names = ordered_joint_names()
    act_ids = np.array([
        mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, f"{f}_{j}_ctrl")
        for f, j in joint_names
    ])
    qpos_ids = np.array([
        model.jnt_qposadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, f"{f}_{j}")]
        for f, j in joint_names
    ])
    return joint_names, act_ids, qpos_ids


def run_headless(model, data, gestures):
    joint_names, act_ids, qpos_ids = build_index_maps(model)
    steps = int(HOLD_SECONDS / model.opt.timestep)
    for gesture in gestures:
        data.ctrl[act_ids] = target_vector(gesture)
        for _ in range(steps):
            mujoco.mj_step(model, data)
        actual = data.qpos[qpos_ids]
        err = np.abs(actual - np.array(target_vector(gesture)))
        status = "OK" if err.max() < 0.2 else "OUT_OF_TOLERANCE"
        print(f"[{status}] {gesture:10s} max|err|={err.max():.4f} rad mean|err|={err.mean():.4f} rad")


def run_viewer(model, data, gestures):
    import mujoco.viewer  # 지연 임포트 — GUI 불필요 시(headless) 의존성 회피

    joint_names, act_ids, qpos_ids = build_index_maps(model)
    idx = 0
    with mujoco.viewer.launch_passive(model, data) as viewer:
        last_switch = time.time()
        data.ctrl[act_ids] = target_vector(gestures[idx])
        while viewer.is_running():
            mujoco.mj_step(model, data)
            if time.time() - last_switch > HOLD_SECONDS:
                idx = (idx + 1) % len(gestures)
                data.ctrl[act_ids] = target_vector(gestures[idx])
                print(f"-> {gestures[idx]}")
                last_switch = time.time()
            viewer.sync()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--headless", action="store_true", help="뷰어 없이 콘솔 검증만 수행")
    ap.add_argument("--gesture", choices=list(GESTURES), default=None,
                     help="지정 시 해당 자세만 유지(순환 안 함)")
    args = ap.parse_args()

    model = mujoco.MjModel.from_xml_path(MODEL_PATH)
    data = mujoco.MjData(model)

    gestures = [args.gesture] if args.gesture else STATE_TRANSITION_SEQUENCE

    if args.headless:
        run_headless(model, data, gestures)
    else:
        run_viewer(model, data, gestures)


if __name__ == "__main__":
    main()
