# Captures

Offscreen renders from `sim_dual_arm` via `mujoco.Renderer` (EGL).

| Folder | Description |
|--------|-------------|
| `scene/` | Static scene snapshots (iso/front/top/pinky/omxf) |
| `arm_motion/` | Dual-arm motion sequences with key frames + animation GIF |
| `combo/` | Combined arm + gripper + OMX-F motion |
| `gripper2/` | Gripper open/close close-ups (OpenArm + OMX-F) |
| `pinky_move/`, `pinky2/`, `pinky3/` | vicpinky differential drive tests |
| `env/` | Scene with floor + skybox + sun light |
| `lit/` | Scene with MJCF headlight |
| `sim_view/` | Early renders before lighting fix |

Files here are excluded from git via `.gitignore`.
