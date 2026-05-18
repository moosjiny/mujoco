# CLAUDE.md — moosjiny/mujoco

## Overview

This repository is a **Dual-Arm MuJoCo Digital Twin** — a physics simulation of a bimanual robotic system built with MuJoCo 3.7.0. The simulated system consists of two OpenArm follower arms, an OMX-F follower arm, and a Vic Pinky mobile base, visualized via Rerun SDK and managed through a FastAPI status dashboard. Optional ROS 2 Jazzy integration provides RViz and interactive-marker IK.

The repo also serves as an **Obsidian knowledge vault** — session notes, troubleshooting docs, and daily logs coexist with code.

**Agent callsign:** Moojoco — this repo's designated AI agent within the ROOPS multi-agent system.

---

## Repository Structure

```
scratch/build_mjcf.py            # SINGLE SOURCE OF TRUTH — regenerates urdf/dual_openarm.xml
urdf/
  dual_openarm.xml               # Compiled MJCF (do not hand-edit; regenerate via build_mjcf.py)
  dual_openarm.urdf              # OpenArm URDF with STL mesh refs + damping
  omx_f.urdf                     # Reference only; meshes from system ROS path
  vicpinky.urdf                  # Reference only; chassis defined in build_mjcf.py
meshes/                          # OpenArm STL/OBJ assets
scripts/
  sim_dual_arm.py               # Main simulation loop (MuJoCo + Rerun)
  sim_interactive_ik.py         # Standalone IK demo (no ROS required)
  sim_ros2_ik.py                # ROS 2-integrated IK with interactive markers
  start_all.sh                  # Launch sim + dashboard (no ROS)
  start_full_sim.sh             # Full stack: sim + ROS 2 + RViz + IK markers
  check_can.py                  # CAN bus hardware health check
  setup_can.sh / setup_can_fd.sh   # Configure CAN / CAN-FD interfaces
  teleop_left.sh                # Teleoperation helper for left arm
  rviz_interactive_marker.py    # RViz 2 interactive marker IK server
  run_dashboard.sh              # Dashboard-only launcher
dashboard/
  main.py                       # FastAPI status dashboard (port 8000)
  templates/                    # Jinja2 HTML templates
config/
  dual_arm_config.yaml          # Hardware: CAN buses, serial ports, cameras
backups/
  2026-05-13_vicpinky_orbit/   # Reference snapshot — diff against this if XML drifts
scratch/
  build_mjcf.py                # Model builder (single source of truth for MJCF)
  _ntfy_fmt.py                 # NTFY notification formatter
  *.py                         # One-off diagnostic/debug scripts
docs/
  10_Daily_Logs/               # Per-session Obsidian progress logs
  30_Troubleshooting/          # Issue resolutions and prevention guides
.obsidian/                     # Obsidian vault config (do not modify)
SESSION_*.md                   # Session reports at repo root (Obsidian notes)
00_Dashboard.md                # Obsidian project dashboard
rviz_dual_arms.rviz            # RViz 2 configuration
```

---

## Environment Setup

### Python venv (system Python 3.12)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

The venv is expected at `/home/moos/dev_ws/dual_arms/venv` by `start_all.sh`. Update the path variable in that script if working on a different machine.

### ROS 2 system package (required for OMX-F meshes)

```bash
sudo apt install ros-jazzy-open-manipulator-description
```

OMX-F STL meshes are loaded from `/opt/ros/jazzy/share/open_manipulator_description/meshes/omx_f/`.

### Rendering environment variable

```bash
export MUJOCO_GL=egl   # EGL for stable headless rendering on Linux
```

---

## Running the Simulation

### Minimal (no ROS 2)

```bash
bash scripts/start_all.sh
```

- MuJoCo native viewer + Rerun stream → http://localhost:9090
- FastAPI dashboard → http://localhost:8000

### Full stack (requires ROS 2 Jazzy + `pyyaml` in venv)

```bash
bash scripts/start_full_sim.sh
```

Adds `robot_state_publisher`, RViz 2, and interactive-marker IK target server.

> **Known issue:** The ROS 2 IK path currently crashes — `target_left`/`target_right` mocap bodies are missing from the generated model. Add them to `scratch/build_mjcf.py` before using this flow.

### Regenerate the MJCF model

```bash
python scratch/build_mjcf.py
```

All structural changes (joint origins, geometry, damping, lighting, environment) go in `build_mjcf.py`. The output `urdf/dual_openarm.xml` is checked in as a convenience but should never be hand-edited.

---

## Key Conventions

### Model editing
- Edit `scratch/build_mjcf.py`, never `urdf/dual_openarm.xml` directly.
- After regenerating, diff against `backups/2026-05-13_vicpinky_orbit/` to detect unexpected drift.
- `lerobot/` is intentionally untracked; install upstream via pip if needed.
- Render captures land in `captures/` (gitignored).

### Hardware configuration (`config/dual_arm_config.yaml`)
| Component | Interface | Config |
|-----------|-----------|--------|
| Left follower arm | CAN-FD `can0` | 1 Mbps nominal / 5 Mbps data |
| Right follower arm | CAN-FD `can1` | 1 Mbps nominal / 5 Mbps data |
| Left leader arm | Dynamixel `/dev/ttyUSB0` | 1 Mbps |
| Right leader arm | Dynamixel `/dev/ttyUSB1` | 1 Mbps |
| Top camera | OpenCV index 0 | — |
| Left wrist camera | OpenCV index 1 | — |
| Right wrist camera | OpenCV index 2 | — |

### Obsidian vault conventions
- Session reports: `SESSION_YYYY-MM-DD_<topic>.md` at repo root.
- Internal links use `[[path/to/doc]]` syntax — do not break them when moving files.
- Do not modify `.obsidian/` directory contents.

### Gitignore highlights
- `captures/` — render output
- `venv/` — Python environment
- `lerobot/` — upstream dependency

---

## Dependency Highlights

| Package | Version | Purpose |
|---------|---------|---------|
| mujoco | 3.7.0 | Physics simulation |
| rerun-sdk | 0.31.3 | Real-time 3D visualization |
| fastapi | 0.136.1 | Status dashboard API |
| uvicorn | 0.46.0 | ASGI server |
| python-can | 4.6.1 | CAN bus interface |
| numpy | 2.4.4 | Numerical operations |
| scipy | 1.17.1 | IK computations |
| trimesh | 4.12.0 | Mesh processing |

---

## ROOPS Multi-Agent Context

This repo participates in **ROOPS** (Robot-Oriented Operation/Programming System), a framework that treats robot components as standardized software objects independent of hardware.

### Agent role
- **Callsign:** Moojoco
- **Domain:** MuJoCo digital twin — model integrity, simulation health, visualization
- **Counterparts:** Aegis (Isaac Sim server), Recon (client-side)

### Communication infrastructure
- NTFY server: `http://hyperbook.com:8880` (plain HTTP — TLS not yet configured)
- Endpoint configured in `~/.roops_moojoco_topics.env` — **never commit this file**
- Topic names and credentials must not appear in committed code or documentation

### Security notes (current as of 2026-05-18)
- Both `moosjiny/mujoco` and `moosjiny/dual_arms` are **private** GitHub repos.
- Clone/pull requires SSH key or personal access token.
- Unauthenticated `api.github.com` / `raw.githubusercontent.com` requests return HTTP 404 — use authenticated API or SSH clone for L1 verification.
- NTFY server runs plain HTTP (port 8880); TLS migration pending.

---

## Port Reference

| Port | Service |
|------|---------|
| 8000 | FastAPI dashboard |
| 9090 | Rerun web viewer |

---

## Known Issues / Open Items

| # | Issue | Status |
|---|-------|--------|
| 1 | ROS 2 IK (`sim_ros2_ik.py`) crashes — `target_left`/`target_right` mocap bodies not in model | Open |
| 2 | OMX-F meshes require ROS system package; not bundled | By design |
| 3 | NTFY server on plain HTTP (port 8880) | TLS pending |
| 4 | `roops-agent` R/W credentials exposed in `roops-comm` channel (2026-05-18) | Rotate immediately |
| 5 | L1 GitHub verification requires auth token (repos private since 2026-05-18) | Moojoco needs fine-grained PAT from admin |
