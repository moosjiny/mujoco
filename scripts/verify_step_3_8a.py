"""Moojoco cross-verification of Step 3.8a cuRobo bimanual action server.

Loads the local MJCF dual-arm model and replays a cuRobo trajectory (worker
output schema: list of 14-float joint vectors over left_joint_1..7,
right_joint_1..7) to measure physical validity from a MuJoCo vantage Aegis's
Isaac Sim cannot directly see:

  A. Joint-limit violation rate                (Phase 3 S3 gate: <0.1%)
  B. End-effector FK pose vs requested target  (cuRobo IK claim: ~0 mm)
  C. Self-collision frames                     (must be 0)
  D. Trajectory smoothness — peak jerk         (yaml limit: 500 rad/s^3)

Modes:
  --fixture <path>     replay a captured worker response JSON
  --synthetic          generate a cosine-lerp trajectory matching the
                       worker's _lerp() math, from zeros to a chosen joint
                       goal (gate B vacuous in this mode)

The harness has no cuRobo dependency — only mujoco + numpy. Run on RTX 4070
or any host with the MJCF.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import mujoco
import numpy as np

CUROBO_JOINT_ORDER = [
    "left_joint_1", "left_joint_2", "left_joint_3", "left_joint_4",
    "left_joint_5", "left_joint_6", "left_joint_7",
    "right_joint_1", "right_joint_2", "right_joint_3", "right_joint_4",
    "right_joint_5", "right_joint_6", "right_joint_7",
]
TOOL_FRAMES = ["left_link7", "right_link7"]
STEP_DT_S = 1.0 / 60.0           # action server's declared trajectory step
MAX_JERK_LIMIT = 500.0           # rad/s^3 (from dual_openarm_curobo.yml)
JOINT_LIMIT_VIOLATION_BUDGET = 0.001   # 0.1% — Phase 3 S3 gate
FK_POS_TOL_MM = 1.0
FK_ORI_TOL_DEG = 1.0


def load_mjcf(path: Path):
    model = mujoco.MjModel.from_xml_path(str(path))
    data = mujoco.MjData(model)
    return model, data


def resolve_joint_qpos_indices(model, joint_names: list[str]) -> list[int]:
    idx = []
    for n in joint_names:
        jid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, n)
        if jid < 0:
            raise KeyError(f"joint {n!r} not in MJCF")
        idx.append(int(model.jnt_qposadr[jid]))
    return idx


def resolve_body_id(model, name: str) -> int:
    bid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, name)
    if bid < 0:
        raise KeyError(f"body {name!r} not in MJCF")
    return int(bid)


def cosine_lerp(start: np.ndarray, goal: np.ndarray, n: int) -> np.ndarray:
    """Mirrors curobo_plan_worker._lerp — half-cosine ease over n steps."""
    out = np.empty((n, len(start)))
    for i in range(n):
        t = (1 - np.cos(np.pi * i / max(n - 1, 1))) / 2
        out[i] = (1 - t) * start + t * goal
    return out


def quat_angle_deg(q1: np.ndarray, q2: np.ndarray) -> float:
    """Angle between two unit quaternions (mujoco order: w,x,y,z) in degrees."""
    dot = abs(float(np.clip(np.dot(q1, q2), -1.0, 1.0)))
    return float(np.degrees(2 * np.arccos(dot)))


def gate_a_joint_limits(model, joint_indices: list[int],
                        traj: np.ndarray) -> dict:
    n_steps, n_dof = traj.shape
    n_samples = n_steps * n_dof
    violations = 0
    per_joint = []
    for c, qpos_addr in enumerate(joint_indices):
        # find the jnt_id back from qpos_addr
        jid = int(np.where(model.jnt_qposadr == qpos_addr)[0][0])
        if model.jnt_limited[jid]:
            lo, hi = model.jnt_range[jid]
            col = traj[:, c]
            mask = (col < lo) | (col > hi)
            v = int(mask.sum())
            violations += v
            if v:
                per_joint.append({
                    "joint": CUROBO_JOINT_ORDER[c],
                    "violations": v,
                    "range": [float(lo), float(hi)],
                    "min_seen": float(col.min()),
                    "max_seen": float(col.max()),
                })
    rate = violations / n_samples if n_samples else 0.0
    return {
        "violations": violations,
        "samples": n_samples,
        "rate": rate,
        "rate_budget": JOINT_LIMIT_VIOLATION_BUDGET,
        "passed": rate < JOINT_LIMIT_VIOLATION_BUDGET,
        "per_joint": per_joint,
    }


def gate_b_fk_target(model, data, joint_indices: list[int],
                     traj: np.ndarray, targets: dict | None) -> dict:
    if targets is None:
        return {"skipped": "no target poses provided (synthetic mode)"}
    final_q = traj[-1]
    data.qpos[:] = 0.0
    for c, idx in enumerate(joint_indices):
        data.qpos[idx] = final_q[c]
    mujoco.mj_forward(model, data)

    results = []
    overall_pass = True
    for side, body_name in zip(("left", "right"), TOOL_FRAMES):
        if side not in targets:
            continue
        tgt = np.asarray(targets[side], dtype=float)
        # worker request format: [x,y,z, qx,qy,qz,qw] (scalar-last)
        tgt_pos = tgt[:3]
        tgt_quat_wxyz = np.array([tgt[6], tgt[3], tgt[4], tgt[5]])
        bid = resolve_body_id(model, body_name)
        ee_pos = data.xpos[bid].copy()
        ee_quat = data.xquat[bid].copy()  # mujoco order: w,x,y,z
        pos_err_mm = float(np.linalg.norm(ee_pos - tgt_pos) * 1000.0)
        ori_err_deg = quat_angle_deg(ee_quat, tgt_quat_wxyz)
        passed = (pos_err_mm <= FK_POS_TOL_MM
                  and ori_err_deg <= FK_ORI_TOL_DEG)
        overall_pass = overall_pass and passed
        results.append({
            "side": side, "body": body_name,
            "pos_err_mm": pos_err_mm, "ori_err_deg": ori_err_deg,
            "passed": passed,
        })
    return {
        "passed": overall_pass,
        "pos_tol_mm": FK_POS_TOL_MM,
        "ori_tol_deg": FK_ORI_TOL_DEG,
        "frames": results,
    }


BIMANUAL_BODY_PREFIXES = (
    "base_plate", "central_pillar", "shoulder_block",
    "left_base_link", "left_link", "left_finger",
    "right_base_link", "right_link", "right_finger",
)

# Pulled from urdf/dual_openarm_curobo.yml -> kinematics.self_collision_ignore.
# Pairs here are allowed to touch; anything else in the bimanual chain that
# overlaps counts as a violation cuRobo would flag if its collision_spheres
# weren't empty.
CUROBO_IGNORE_PAIRS = frozenset(
    frozenset((a, b))
    for a, blist in {
        "base_plate": ["central_pillar"],
        "central_pillar": ["base_plate", "shoulder_block"],
        "shoulder_block": ["central_pillar",
                           "left_base_link", "right_base_link"],
        "left_base_link":  ["shoulder_block", "left_link1"],
        "right_base_link": ["shoulder_block", "right_link1"],
        "left_link1":  ["left_base_link", "left_link2"],
        "left_link2":  ["left_link1", "left_link3"],
        "left_link3":  ["left_link2", "left_link4"],
        "left_link4":  ["left_link3", "left_link5"],
        "left_link5":  ["left_link4", "left_link6"],
        "left_link6":  ["left_link5", "left_link7"],
        "left_link7":  ["left_link6", "left_finger_1", "left_finger_2"],
        "left_finger_1":  ["left_link7"],
        "left_finger_2":  ["left_link7"],
        "right_link1": ["right_base_link", "right_link2"],
        "right_link2": ["right_link1", "right_link3"],
        "right_link3": ["right_link2", "right_link4"],
        "right_link4": ["right_link3", "right_link5"],
        "right_link5": ["right_link4", "right_link6"],
        "right_link6": ["right_link5", "right_link7"],
        "right_link7": ["right_link6", "right_finger_1", "right_finger_2"],
        "right_finger_1": ["right_link7"],
        "right_finger_2": ["right_link7"],
    }.items()
    for b in blist
)


def _is_bimanual_body(name: str) -> bool:
    return any(name == p or name.startswith(p) for p in BIMANUAL_BODY_PREFIXES)


def _curobo_allows(n1: str, n2: str) -> bool:
    return frozenset((n1, n2)) in CUROBO_IGNORE_PAIRS


def gate_c_self_collision(model, data, joint_indices: list[int],
                          traj: np.ndarray) -> dict:
    """Per-waypoint mj_forward + contact count over bimanual bodies only.

    Restricts to pairs where BOTH bodies are part of the bimanual chain that
    cuRobo plans for. Pinky/OMX-F + floor contacts are out of scope here —
    those belong to a different planner and are validated elsewhere.
    Gripper-internal pairs (finger-finger, finger-link7) are also allowed.
    """
    collide_frames = 0
    sample = []
    for k, q in enumerate(traj):
        data.qpos[:] = 0.0
        for c, idx in enumerate(joint_indices):
            data.qpos[idx] = q[c]
        mujoco.mj_forward(model, data)
        ncon = int(data.ncon)
        bad = 0
        for ci in range(ncon):
            con = data.contact[ci]
            g1, g2 = int(con.geom1), int(con.geom2)
            b1 = int(model.geom_bodyid[g1])
            b2 = int(model.geom_bodyid[g2])
            n1 = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_BODY, b1) or ""
            n2 = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_BODY, b2) or ""
            if not (_is_bimanual_body(n1) and _is_bimanual_body(n2)):
                continue
            if _curobo_allows(n1, n2):
                continue
            bad += 1
            if len(sample) < 5:
                sample.append({"step": k, "pair": [n1, n2],
                               "dist_mm": float(con.dist) * 1000.0})
        if bad:
            collide_frames += 1
    return {
        "collide_frames": collide_frames,
        "total_frames": int(traj.shape[0]),
        "sample_pairs": sample,
        "passed": collide_frames == 0,
    }


def gate_d_smoothness(traj: np.ndarray) -> dict:
    if traj.shape[0] < 4:
        return {"skipped": "trajectory too short for jerk estimate",
                "passed": True}
    dt = STEP_DT_S
    vel = np.diff(traj, axis=0) / dt
    acc = np.diff(vel, axis=0) / dt
    jerk = np.diff(acc, axis=0) / dt
    peak = float(np.abs(jerk).max())
    rms = float(np.sqrt(np.mean(jerk ** 2)))
    return {
        "peak_jerk": peak,
        "rms_jerk": rms,
        "limit": MAX_JERK_LIMIT,
        "passed": peak <= MAX_JERK_LIMIT,
    }


def synthetic_fixture(seed: int = 0) -> dict:
    """Mimic worker output: cosine-lerp from zero to a random feasible-ish goal."""
    rng = np.random.default_rng(seed)
    # modest goals — keep within typical joint ranges for arms
    goal = rng.uniform(-0.6, 0.6, size=14)
    start = np.zeros(14)
    traj = cosine_lerp(start, goal, 60)
    return {
        "success": True,
        "joints": list(CUROBO_JOINT_ORDER),
        "trajectory": traj.tolist(),
        "solve_ms": 0.0,
        "_synthetic": True,
        "_targets": None,
    }


def load_fixture(path: Path) -> dict:
    with path.open() as f:
        obj = json.load(f)
    if "trajectory" not in obj or "joints" not in obj:
        raise ValueError("fixture missing 'trajectory' or 'joints'")
    return obj


def reorder_to_curobo(traj: np.ndarray, fixture_joints: list[str]) -> np.ndarray:
    if fixture_joints == CUROBO_JOINT_ORDER:
        return traj
    idx_map = [fixture_joints.index(n) for n in CUROBO_JOINT_ORDER]
    return traj[:, idx_map]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mjcf", default="urdf/dual_openarm.xml")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--fixture", type=Path,
                     help="worker-response JSON to validate")
    src.add_argument("--synthetic", action="store_true",
                     help="generate a cosine-lerp trajectory (no cuRobo)")
    ap.add_argument("--seed", type=int, default=0,
                    help="synthetic mode RNG seed")
    ap.add_argument("--json", action="store_true",
                    help="machine-readable JSON output instead of table")
    args = ap.parse_args()

    mjcf_path = Path(args.mjcf)
    if not mjcf_path.is_absolute():
        mjcf_path = Path(__file__).resolve().parent.parent / mjcf_path
    model, data = load_mjcf(mjcf_path)

    if args.synthetic:
        fixture = synthetic_fixture(args.seed)
    else:
        fixture = load_fixture(args.fixture)

    traj = np.array(fixture["trajectory"], dtype=float)
    fixture_joints = list(fixture["joints"])
    traj = reorder_to_curobo(traj, fixture_joints)
    targets = fixture.get("_targets")  # may be in fixture; None otherwise

    joint_indices = resolve_joint_qpos_indices(model, CUROBO_JOINT_ORDER)

    a = gate_a_joint_limits(model, joint_indices, traj)
    b = gate_b_fk_target(model, data, joint_indices, traj, targets)
    c = gate_c_self_collision(model, data, joint_indices, traj)
    d = gate_d_smoothness(traj)

    summary = {
        "mjcf": str(mjcf_path),
        "trajectory_steps": int(traj.shape[0]),
        "synthetic": bool(args.synthetic),
        "gate_a_joint_limits": a,
        "gate_b_fk_target": b,
        "gate_c_self_collision": c,
        "gate_d_smoothness": d,
    }
    overall = (a.get("passed", False)
               and (b.get("passed", True) or "skipped" in b)
               and c.get("passed", False)
               and d.get("passed", False))
    summary["overall_passed"] = overall

    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        _print_table(summary)
    return 0 if overall else 1


def _print_table(s: dict) -> None:
    print(f"MJCF: {s['mjcf']}")
    print(f"Trajectory steps: {s['trajectory_steps']}  "
          f"synthetic={s['synthetic']}")
    print("-" * 64)
    a = s["gate_a_joint_limits"]
    print(f"A. Joint limits:   {'PASS' if a['passed'] else 'FAIL'}  "
          f"violations={a['violations']}/{a['samples']} "
          f"(rate={a['rate']:.4%}, budget={a['rate_budget']:.2%})")
    for v in a.get("per_joint", []):
        print(f"     - {v['joint']}: {v['violations']}× "
              f"range={v['range']} seen=[{v['min_seen']:.3f}, {v['max_seen']:.3f}]")
    b = s["gate_b_fk_target"]
    if "skipped" in b:
        print(f"B. FK vs target:   SKIPPED ({b['skipped']})")
    else:
        print(f"B. FK vs target:   {'PASS' if b['passed'] else 'FAIL'}  "
              f"(pos≤{b['pos_tol_mm']}mm, ori≤{b['ori_tol_deg']}°)")
        for f in b["frames"]:
            print(f"     - {f['side']}: pos={f['pos_err_mm']:.3f}mm "
                  f"ori={f['ori_err_deg']:.3f}°")
    c = s["gate_c_self_collision"]
    print(f"C. Self-collision: {'PASS' if c['passed'] else 'FAIL'}  "
          f"frames={c['collide_frames']}/{c['total_frames']}")
    for x in c["sample_pairs"][:3]:
        print(f"     - step {x['step']}: {x['pair'][0]} ↔ {x['pair'][1]}")
    d = s["gate_d_smoothness"]
    if "skipped" in d:
        print(f"D. Smoothness:     SKIPPED ({d['skipped']})")
    else:
        print(f"D. Smoothness:     {'PASS' if d['passed'] else 'FAIL'}  "
              f"peak_jerk={d['peak_jerk']:.1f} rms={d['rms_jerk']:.1f} "
              f"limit={d['limit']:.0f} rad/s³")
    print("-" * 64)
    print(f"OVERALL: {'PASS' if s['overall_passed'] else 'FAIL'}")


if __name__ == "__main__":
    sys.exit(main())
