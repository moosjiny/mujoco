---
tags: project/dashboard
status: active
last_updated: 2026-05-08
---

# 🤖 Dual-Arm Digital Twin Dashboard

> [!abstract] Project Overview
> Integrating a dual-arm robotic simulation (MuJoCo) with real-time visualization (Rerun) and a monitoring dashboard (FastAPI).
> **Objective**: Stable physics-based digital twin with collision detection and interactive monitoring.

---

## 🚀 Quick Actions

> [!tip] Start System
> 1. Open Terminal
> 2. Run: `bash scripts/start_all.sh`
> 3. View Dashboard: [http://localhost:8000](http://localhost:8000)

- [ ] [[docs/10_Daily_Logs/2026-05-07_session_progress|Last Session Progress]]
- [ ] [[scripts/sim_dual_arm.py|Main Simulation Script]]
- [ ] [[urdf/dual_openarm.xml|MuJoCo Model (MJCF)]]

---

## 📂 Documentation Map

### 📅 [[docs/10_Daily_Logs/|Daily Logs]]
- [[docs/10_Daily_Logs/2026-05-07_session_progress|2026-05-07: MuJoCo Physics & Dashboard Integration]]
- [[docs/10_Daily_Logs/2026-04-27_session_progress|2026-04-27: Initial Setup]]

### 🏗️ Architecture & Specs
- [[urdf/vicpinky.urdf|ViC-Pinky URDF]]
- [[urdf/omx_f.urdf|OMX-F URDF]]
- [[scratch/build_mjcf.py|MJCF Builder Script]]

### 🛠️ Troubleshooting
- [[docs/30_Troubleshooting/dual_arm_alignment_resolution|Alignment Resolution]]
- [[docs/30_Troubleshooting/dual_arm_prevention_measures|Prevention Measures]]
- [[docs/30_Troubleshooting/alignment_error_report|Error Report]]

---

## 📈 System Status

| Component | Status | Note |
| --- | --- | --- |
| **MuJoCo** | ✅ Active | Using mj_step with Position Control |
| **Rerun** | ✅ Active | Web Viewer on port 9090 |
| **Dashboard** | ✅ Active | FastAPI + WebSocket |
| **Physics** | ✅ Active | Collision detection enabled |

---

> [!info] Next Steps
> - [ ] Fix OMX-F mesh missing issues
> - [ ] Restore ViC-Pinky full details (LiDAR, Column)
> - [ ] Expand sweep demo to all joints
