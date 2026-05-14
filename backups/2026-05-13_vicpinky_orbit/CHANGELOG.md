# 2026-05-13 — vicpinky orbit backup

Snapshot of MJCF + sim_dual_arm.py after this session's enhancements.

## Major changes

### `urdf/dual_openarm.xml`
- **OMX-F**: replaced 8 green-box placeholders with `/opt/ros/jazzy/share/open_manipulator_description/meshes/omx_f/follower_*.stl`
- **OMX-F joints**: added `damping="0.3" frictionloss="0.02" armature="0.001"` (fixed NaN at DOF 19/20/21)
- **vicpinky**: rebuilt to match `vicpinky_description/urdf/robot_core.xacro` (chassis + top plate + 4 pillars + 2 casters + LiDAR mount with STL)
- **vicpinky inertial**: `pos="-0.2 0 0.08" mass="15" diaginertia="0.4 0.6 0.8"` (was `(0, -0.2, 0.15)` mass=55 — toppled)
- **vicpinky freejoint**: added `<freejoint name="pinky_base_free"/>` so the base can move
- **vicpinky wheels**: friction `2.0 0.02 0.001`, damping `0.01`
- **vicpinky casters**: friction `0.05 0.001 0.0001` (low drag)
- **Wheel actuators**: switched from `general` torque (gainprm=10) to `velocity` (kv=150) for clean velocity tracking
- **Visual / environment**: `<visual><headlight/></visual>`, skybox gradient, checker groundplane, sun directional light
- **Solver**: `<option timestep="0.001" integrator="implicitfast"/>` for stability

### `scripts/sim_dual_arm.py`
- After `data.qpos[:] = 0.0`, explicitly restore `pinky_base_free` freejoint: pos `(0, 1.2, 0)`, quat `(1, 0, 0, 0)` — else the zeroed quaternion makes the base orientation invalid
- In control loop: added vicpinky CW orbit controller around the origin
  - Target radius 1.2m, linear speed 0.18 m/s, ~7.7°/s yaw rate
  - PI feedback on yaw error (gain 0.6) and radius error (gain 0.4)
  - Drives `pinky_left_wheel_joint_ctrl` / `pinky_right_wheel_joint_ctrl`

## Verified behavior

- Self-stable: 5s free simulation, qvel max < 0.5
- Combined arms + grippers + OMX-F (5 cycles, 196 frames): no NaN
- vicpinky orbit: 50s → 384° traveled at radius 1.23 ± 0.018m

## Files in this backup
- `urdf/dual_openarm.xml` — current
- `urdf/dual_openarm.xml.pre_omxf_mesh.bak` — before OMX-F mesh adoption
- `urdf/dual_openarm.xml.pre_damping_bak` — before OMX-F damping additions
- `scripts/sim_dual_arm.py` — current
- `.gitignore` — current
- `captures_README.md` — index of capture subfolders
