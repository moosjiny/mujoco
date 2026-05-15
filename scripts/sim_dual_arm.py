import mujoco
import mujoco.viewer
import rerun as rr
import numpy as np
import time
import os
import threading
import trimesh
import json
import urllib.request

# Configuration
URDF_PATH = "/home/moos/dev_ws/dual_arms/urdf/dual_openarm.xml"
MESH_DIR = "/home/moos/dev_ws/dual_arms/meshes/"
DASHBOARD_URL = "http://localhost:8000/update"

# VERSIONED PATHS
ROBOT_ROOT = "world/robot_v4"

# ROOPS Continuum NTFY publishing (no-op if env vars unset).
# Topic name is a secret — only read from MUJOCO_TOPIC_SIM, never log/print/inline.
NTFY_BASE        = os.environ.get("NTFY_BASE", "")
MUJOCO_TOPIC_SIM = os.environ.get("MUJOCO_TOPIC_SIM", "")
SIM_PUBLISH_HZ   = 10

# qpos layout (verified against build_mjcf.py output 2026-05-15):
#   [0:18]   bimanual: left arm(7) + left fingers(2) + right arm(7) + right fingers(2)
#   [18:25]  omxf single arm: joints 1-5 + 2 grippers
#   [25:32]  pinky_base_free: xyz + quat (wxyz)
#   [32:34]  pinky wheels: left, right
QPOS_BIMANUAL_SLICE = (0, 18)
QPOS_OMXF_SLICE     = (18, 25)
QPOS_PINKY_BASE_SLICE  = (25, 32)
QPOS_PINKY_WHEEL_SLICE = (32, 34)

def send_to_dashboard(data_dict):
    try:
        req = urllib.request.Request(DASHBOARD_URL, data=json.dumps(data_dict).encode('utf-8'), headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=0.02) as response:
            pass
    except Exception:
        pass

def _post_sim_state_async(payload_bytes, url):
    try:
        req = urllib.request.Request(url, data=payload_bytes, method="POST",
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=0.2):
            pass
    except Exception:
        pass

def publish_sim_state(data, pinky_body_id):
    if not (NTFY_BASE and MUJOCO_TOPIC_SIM):
        return
    bi0, bi1 = QPOS_BIMANUAL_SLICE
    o0, o1   = QPOS_OMXF_SLICE
    pb0, pb1 = QPOS_PINKY_BASE_SLICE
    pw0, pw1 = QPOS_PINKY_WHEEL_SLICE
    state = {
        "ts": time.time(),
        "bimanual": {"qpos": data.qpos[bi0:bi1].tolist()},
        "omxf":     {"qpos": data.qpos[o0:o1].tolist()},
        "pinky": {
            "base_qpos":  data.qpos[pb0:pb1].tolist(),
            "wheel_qpos": data.qpos[pw0:pw1].tolist(),
            "xpos":       data.xpos[pinky_body_id].tolist() if pinky_body_id >= 0 else None,
        },
    }
    payload = json.dumps(state).encode("utf-8")
    url = f"{NTFY_BASE}/{MUJOCO_TOPIC_SIM}"
    threading.Thread(target=_post_sim_state_async, args=(payload, url), daemon=True).start()

def run_sim():
    # 1. Load MuJoCo Model
    try:
        model = mujoco.MjModel.from_xml_path(URDF_PATH)
        data = mujoco.MjData(model)
    except Exception as e:
        print(f"Failed to load URDF: {e}")
        return

    # 2. Initialize Rerun
    rr.init("OpenArm_WowRobo_V4", spawn=False)
    server_uri = rr.serve_grpc(grpc_port=9876)
    rr.serve_web_viewer(web_port=9090, connect_to=server_uri)
    
    print(f"Digital Twin Simulation (Native + Rerun) started.")

    rr.log("world/floor", rr.Boxes3D(half_sizes=[[1.5, 1.5, 0.001]], colors=[[180, 180, 180]]), static=True)
    
    # Unified Central Base Mesh
    base_mesh_path = os.path.join(MESH_DIR, "base_link.stl")
    if os.path.exists(base_mesh_path):
        base_mesh = trimesh.load(base_mesh_path)
        rr.log(f"{ROBOT_ROOT}/central_base/visual", 
               rr.Mesh3D(vertex_positions=base_mesh.vertices * 0.001,
                         triangle_indices=base_mesh.faces,
                         vertex_normals=base_mesh.vertex_normals,
                         vertex_colors=np.tile([180, 180, 180], (len(base_mesh.vertices), 1))), static=True)

    # Mesh Mapping
    mesh_map = {
        "link1": "link1.stl", "link2": "link2.stl", "link3": "link3.stl",
        "link4": "link4.stl", "link5": "link5.stl", "link6": "link6.stl", "link7": "link7.stl"
    }

    # Pre-log Arm Meshes
    for name, file in mesh_map.items():
        path = os.path.join(MESH_DIR, file)
        if os.path.exists(path):
            try:
                mesh = trimesh.load(path)
                num_v = len(mesh.vertices)
                STL_OFFSETS = {
                    "base_link": [0.0, 0.0, 0.0], "link1": [0.0, 0.0, 62.5],
                    "link2": [-30.1, 0.0, 122.5], "link3": [0.0, 0.0, 188.75],
                    "link4": [0.0, 31.5, 342.5], "link5": [0.0, 0.0, 438.0],
                    "link6": [37.5, 0.0, 558.5], "link7": [0.0, 0.0, 558.5]
                }
                offset_3d = np.array(STL_OFFSETS.get(name, [0.0, 0.0, 0.0]))
                n_mesh = mesh.vertex_normals
                v_l = (mesh.vertices - offset_3d) * 0.001
                colors_l = np.tile([40, 80, 200], (num_v, 1))
                rr.log(f"{ROBOT_ROOT}/left_{name}/visual", 
                       rr.Mesh3D(vertex_positions=v_l, triangle_indices=mesh.faces, vertex_normals=n_mesh, vertex_colors=colors_l), static=True)
                v_r_raw = mesh.vertices.copy()
                offset_3d_r = offset_3d.copy()
                if name in ["link1", "link2", "link3"]:
                    v_r_raw[:, 0] = -v_r_raw[:, 0]
                    offset_3d_r[0] = -offset_3d[0]
                v_r = (v_r_raw - offset_3d_r) * 0.001
                colors_r = np.tile([200, 40, 40], (num_v, 1))
                rr.log(f"{ROBOT_ROOT}/right_{name}/visual", 
                       rr.Mesh3D(vertex_positions=v_r, triangle_indices=mesh.faces, vertex_normals=n_mesh, vertex_colors=colors_r), static=True)
            except Exception as e: print(f"Error loading {file}: {e}")

    # Gripper meshes
    finger_dir = os.path.join(MESH_DIR, "gripper")
    finger_parts = [("finger_0.obj", [180, 180, 180]), ("finger_1.obj", [30, 30, 30])]
    NF_OFFSET_MM = np.array([0.0,  50.0, 673.001])
    FL_OFFSET_MM = np.array([0.0, -50.0, 673.001])
    for part_file, color in finger_parts:
        p = os.path.join(finger_dir, part_file)
        if os.path.exists(p):
            try:
                fmesh = trimesh.load(p)
                v_raw = np.asarray(fmesh.vertices)
                v_nf = (v_raw - NF_OFFSET_MM) * 0.001
                v_fl_raw = v_raw.copy(); v_fl_raw[:, 1] = -v_fl_raw[:, 1]
                v_fl = (v_fl_raw - FL_OFFSET_MM) * 0.001
                faces_fl = fmesh.faces[:, ::-1]
                for side in ("left", "right"):
                    rr.log(f"{ROBOT_ROOT}/{side}_finger_1/visual_{part_file}",
                           rr.Mesh3D(vertex_positions=v_nf, triangle_indices=fmesh.faces, vertex_normals=fmesh.vertex_normals, vertex_colors=np.tile(color, (len(v_nf), 1))), static=True)
                    rr.log(f"{ROBOT_ROOT}/{side}_finger_2/visual_{part_file}",
                           rr.Mesh3D(vertex_positions=v_fl, triangle_indices=faces_fl, vertex_colors=np.tile(color, (len(v_fl), 1))), static=True)
            except Exception as e: print(f"Error loading finger mesh {part_file}: {e}")

    # Sweep Setup
    SWEEP_DURATION = 4.0
    sweep_items = []
    for i in range(model.njnt):
        jn = model.joint(i).name
        if "finger_joint2" in jn: continue
        pair_idx = None
        label = jn
        if "finger_joint1" in jn:
            side = jn.split("_")[0]
            pair_idx = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, f"{side}_finger_joint2")
            label = f"{side}_gripper"
        sweep_items.append((i, label, pair_idx))

    data.qpos[:] = 0.0
    # Restore pinky_base freejoint (qpos[:] = 0 zeroes the quaternion → invalid)
    pinky_jnt = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, "pinky_base_free")
    if pinky_jnt >= 0:
        qadr = model.jnt_qposadr[pinky_jnt]
        data.qpos[qadr:qadr+3] = [0.0, 1.2, 0.0]
        data.qpos[qadr+3:qadr+7] = [1.0, 0.0, 0.0, 0.0]
    mujoco.mj_forward(model, data)

    # Vicpinky orbit controller — slow clockwise circle around dual arms (origin)
    PINKY_LW_ACT = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, "pinky_left_wheel_joint_ctrl")
    PINKY_RW_ACT = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, "pinky_right_wheel_joint_ctrl")
    PINKY_BASE_BID = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "pinky_base")
    ORBIT_V = 0.18           # m/s linear speed
    ORBIT_R = 1.2            # m target radius from origin
    WHEEL_R = 0.0825
    WHEEL_SEP = 0.475
    ORBIT_OMEGA = -ORBIT_V / ORBIT_R  # negative = CW orbit (robot starts at (0,1.2) facing +x)

    # 3. Launch Native Viewer and Simulation Loop
    with mujoco.viewer.launch_passive(model, data) as viewer:
        start_time = time.time()
        last_render_time = 0
        last_dashboard_time = 0
        last_sim_pub_time = 0
        RENDER_FPS = 30
        DASHBOARD_FPS = 10
        
        while viewer.is_running():
            t = time.time() - start_time
            cycle_t = t % (SWEEP_DURATION * len(sweep_items))
            item_idx = int(cycle_t // SWEEP_DURATION)
            phase = (cycle_t % SWEEP_DURATION) / SWEEP_DURATION

            j_idx, label, pair_idx = sweep_items[item_idx]
            lo, hi = model.jnt_range[j_idx]
            center = (lo + hi) / 2.0
            amp = (hi - lo) / 2.0
            target = center + amp * np.sin(phase * 2 * np.pi)

            # Control
            data.ctrl[:] = 0.0
            j_name = model.joint(j_idx).name
            side = j_name.split("_")[0]
            act_name = j_name + "_ctrl" if "finger" not in j_name else side + "_finger_ctrl"
            act_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, act_name)
            if act_id >= 0:
                data.ctrl[act_id] = target

            # Vicpinky orbit: feedback toward target tangent direction
            if PINKY_LW_ACT >= 0 and PINKY_RW_ACT >= 0 and PINKY_BASE_BID >= 0:
                px, py = data.xpos[PINKY_BASE_BID, 0], data.xpos[PINKY_BASE_BID, 1]
                # Current heading from quaternion (yaw)
                qw, qx, qy, qz = (data.xquat[PINKY_BASE_BID, 0],
                                  data.xquat[PINKY_BASE_BID, 1],
                                  data.xquat[PINKY_BASE_BID, 2],
                                  data.xquat[PINKY_BASE_BID, 3])
                yaw = np.arctan2(2*(qw*qz + qx*qy), 1 - 2*(qy*qy + qz*qz))
                # Desired tangent direction for CW orbit around origin:
                # At pos (px,py), radial = (px,py)/r, tangent_CW = (py, -px)/r
                r = np.hypot(px, py) + 1e-6
                desired_yaw = np.arctan2(-px, py)   # tangent CW: (+py, -px)
                yaw_err = np.arctan2(np.sin(desired_yaw - yaw), np.cos(desired_yaw - yaw))
                # Also correct radial offset
                radius_err = r - ORBIT_R
                yaw_correction = 0.6 * yaw_err - 0.4 * radius_err
                omega_robot = ORBIT_OMEGA + yaw_correction
                v_fwd = ORBIT_V
                omega_L = (v_fwd - omega_robot * WHEEL_SEP / 2.0) / WHEEL_R
                omega_R = (v_fwd + omega_robot * WHEEL_SEP / 2.0) / WHEEL_R
                data.ctrl[PINKY_LW_ACT] = np.clip(omega_L, -10, 10)
                data.ctrl[PINKY_RW_ACT] = np.clip(omega_R, -10, 10)

            # Step
            for _ in range(10):
                mujoco.mj_step(model, data)

            # Sync Dashboard
            if t - last_dashboard_time > (1.0 / DASHBOARD_FPS):
                update_data = {
                    "left": {
                        "joints": [float(data.qpos[model.jnt_qposadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, f"left_joint_{i+1}")]]) for i in range(7)],
                        "torque": [float(data.qfrc_actuator[model.jnt_dofadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, f"left_joint_{i+1}")]]) for i in range(7)],
                        "gripper": float(data.qpos[model.jnt_qposadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, "left_finger_joint1")]])
                    },
                    "right": {
                        "joints": [float(data.qpos[model.jnt_qposadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, f"right_joint_{i+1}")]]) for i in range(7)],
                        "torque": [float(data.qfrc_actuator[model.jnt_dofadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, f"right_joint_{i+1}")]]) for i in range(7)],
                        "gripper": float(data.qpos[model.jnt_qposadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, "right_finger_joint1")]])
                    },
                    "status": "HYBRID_SIM"
                }
                send_to_dashboard(update_data)
                last_dashboard_time = t

            # Publish sim-state to ROOPS NTFY (no-op if env vars unset)
            if t - last_sim_pub_time > (1.0 / SIM_PUBLISH_HZ):
                publish_sim_state(data, PINKY_BASE_BID)
                last_sim_pub_time = t

            # Sync Rerun
            if t - last_render_time > (1.0 / RENDER_FPS):
                rr.log("status/sweep", rr.TextDocument(f"[{item_idx + 1}/{len(sweep_items)}] {label}\nTarget: {target:+.3f}"))
                for i in range(model.nbody):
                    b_name = model.body(i).name
                    if not b_name or b_name == "world" or "target" in b_name: continue
                    pos = data.xpos[i]
                    quat = data.xquat[i]
                    rr_quat = [quat[1], quat[2], quat[3], quat[0]]
                    rr.log(f"{ROBOT_ROOT}/{b_name}", rr.Transform3D(translation=pos, rotation=rr.Quaternion(xyzw=rr_quat)))
                viewer.sync()
                last_render_time = t

            time.sleep(0.01)

if __name__ == "__main__":
    run_sim()
