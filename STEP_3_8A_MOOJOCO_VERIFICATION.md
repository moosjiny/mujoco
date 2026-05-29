# Step 3.8a cuRobo bimanual action server — Moojoco cross-verification

**Reviewer:** Moojoco (RTX 4070, MuJoCo 3.7.0)
**Subject:** `dual_arms_integration` @ `51d6f87` — `scripts/curobo_bimanual_action_server.py` + `scripts/curobo_plan_worker.py`
**Reference spec:** `docs/PHASE3_ROBOT_MOTION_PLAN_20260514.md` §3.3 pivot + §3.8a
**Date:** 2026-05-29 KST
**Harness:** `scripts/verify_step_3_8a.py` (this repo) — `--synthetic` smoke test passed mechanically; static-analysis findings dominate.

---

## TL;DR

Step 3.8a code lands a working action server skeleton, but **three architectural deviations from the plan + one result-message correctness bug** are unsurfaced. Most consequential: the worker uses **cuRobo InverseKinematics + cosine lerp**, not MotionGen — there is **no collision-aware planning** anywhere in the path. Combined with cuRobo's `collision_spheres: {}` (empty) in `dual_openarm_curobo.yml`, the system performs **no self-collision checking**. Moojoco's MJCF measurement shows the rest pose — which is exactly where every worker-output trajectory starts — has the central pillar geometry **intruding 14.5 mm into `left_link1` and `right_link1`** (3.9 mm into `link2`). Every emitted trajectory's first frames are in self-collision per MuJoCo measurement.

---

## Findings

### F-1 (Bug, correctness) — Result message does not carry the planned trajectory

`scripts/curobo_bimanual_action_server.py` lines 117-130:

```python
result_traj = JointTrajectory()
result_traj.joint_names = joints
for i, wp in enumerate(traj_data):
    pt = JointTrajectoryPoint()
    pt.positions = [float(v) for v in wp]
    t_ns = int(i * STEP_DT_S * 1e9)
    pt.time_from_start = Duration(...)
    result_traj.points.append(pt)

goal_handle.succeed()
result = FollowJointTrajectory.Result()
result.error_code = FollowJointTrajectory.Result.SUCCESSFUL
return result
```

- `FollowJointTrajectory.Result` has fields `error_code` and `error_string` only — no trajectory field.
- `result_traj` is built but never assigned to anything and never returned.
- The docstring (line 9) claims "Result: planned trajectory (joint_names + waypoints at 60 Hz)" — this is **not true** for clients of this server.

**Impact:** action clients receive only success/fail; the trajectory is opaque. Step 3.8b (viewer as action client) cannot drive `set_joint_positions()` from the returned data as the spec implies.

**Fix:** either (a) move to a custom `BimanualPlanMotion` action with a trajectory output field (slated for 3.8b per docstring), or (b) publish the result trajectory on a side topic, or (c) re-use `FollowJointTrajectory.Goal` semantics by treating this as a true trajectory-execution action.

---

### F-2 (Architecture deviation, undeclared) — IK + cosine lerp instead of MotionGen

Plan §3.3 original: *"Wrap cuRobo's `MotionGen` to plan a trajectory."*
Plan §3.8a: *"Loads cuRobo from `urdf/dual_openarm_curobo.yml`."*
Plan §3.8 header: *"Bimanual grasp IK + OMX-F receive pose (cuRobo action server + handoff)."*

Actual `curobo_plan_worker.py`:

```python
from curobo.inverse_kinematics import InverseKinematics, InverseKinematicsCfg
cfg = InverseKinematicsCfg.create(robot=YAML_PATH, num_seeds=32)
ik = InverseKinematics(cfg)
...
result = IK.solve_pose(goal)
...
goal_js = result.js_solution.position[0, 0].cpu().numpy()
default_js = IK.default_joint_state.position.cpu().numpy()
traj = _lerp(default_js, goal_js, TRAJ_STEPS)
```

The worker computes IK to the goal pose then returns a **half-cosine interpolation between the default joint state and that IK solution** (line 104). This is not motion planning — there is no obstacle awareness, no joint-limit enforcement during interpolation (only at the goal sample), no time parameterisation against velocity/acceleration limits.

**Impact:** any obstacle (the central pillar, the OMX-F arms on Pinky's deck, the worker character, walls) on the straight cosine path from default to goal is ignored.

**Fix:** replace `InverseKinematicsCfg.create` + `_lerp` with `MotionGenConfig` + `MotionGen.plan_single`. The yaml already has `max_acceleration` and `max_jerk` populated for that path.

---

### F-3 (Configuration gap) — `collision_spheres: {}` disables all cuRobo collision checking

`urdf/dual_openarm_curobo.yml` line 7:
```yaml
collision_spheres: {}
collision_link_names: []
```

cuRobo's collision checks require sphere primitives per link. With both fields empty, the solver has nothing to check against and reports collision-free regardless of geometry. The `self_collision_ignore` table at lines 172-242 is therefore moot — it controls allowable contacts between spheres that don't exist.

**Impact:** even if F-2 were resolved (switching to MotionGen), MotionGen would emit "collision-free" plans without ever testing collision.

**Fix:** populate `collision_spheres` per link (cuRobo's `urdf_helper` can auto-generate from the URDF) and re-list `collision_link_names`.

---

### F-4 (Cross-vantage finding) — MJCF rest-pose self-intrusion at every trajectory start

`scripts/verify_step_3_8a.py` Gate C, synthetic-mode run (this repo, MuJoCo 3.7.0):

| Pair | Distance | Frames affected |
|---|---|---|
| `central_pillar ↔ left_link1`  | **−14.5 mm** | 60/60 |
| `central_pillar ↔ left_link2`  | −3.9 mm | 60/60 |
| `central_pillar ↔ right_link1` | **−14.5 mm** | 60/60 |
| `central_pillar ↔ right_link2` | −3.9 mm | 60/60 |
| `left_link5 ↔ left_link7`   | −3.0 mm | 60/60 |
| `right_link5 ↔ right_link7` | −3.0 mm | 60/60 |

(Negative distance = interpenetration. Filter applied is cuRobo's own `self_collision_ignore` table.)

The worker's lerp starts from `default_joint_state = [0]*14` (zero joints). The MJCF model in this repo (`urdf/dual_openarm.xml`, built by `scratch/build_mjcf.py`) places the central pillar geometry inside `link1` and `link2` at that rest pose.

Three non-exclusive explanations:
1. **MJCF defect** — `build_mjcf.py` emits link or pillar geometry sized differently from the URDF used by cuRobo (URDF has no collision spheres so neither side checks).
2. **URDF defect** — both models share the same collision overlap; only cuRobo's empty spheres hide it.
3. **cuRobo ignore-list defect** — `central_pillar ↔ left_link1/2` and `right_link1/2` and `left_link5 ↔ left_link7` should be added to `self_collision_ignore` if these contacts are by-design structural mounting.

**Impact:** depending on which of the three is right — Aegis side cannot see this without populating cuRobo collision spheres or running an external collision check. It is the kind of measurement Moojoco's seat is for.

**Suggested next step:** Aegis (or the model author) clarifies whether the rest-pose overlap is by design. If yes → expand cuRobo `self_collision_ignore`. If no → diff MJCF vs URDF geometry in `build_mjcf.py` and the OpenArm URDF.

---

### F-5 (Spec abuse, partially acknowledged) — `FollowJointTrajectory` shoehorned as IK request

Action goal packing (`scripts/curobo_bimanual_action_server.py` lines 52-60):

```python
positions = list(pts[0].positions)
if len(positions) < 14:
    return None, None, f"expected 14 values (left7+right7), got {len(positions)}"
return positions[:7], positions[7:14], None
```

The action server expects `trajectory.points[0].positions` to contain **14 floats packed as `[lx, ly, lz, lqx, lqy, lqz, lqw, rx, ry, rz, rqx, rqy, rqz, rqw]`** (left + right Cartesian pose), with `trajectory.joint_names = ["__goal_left__", "__goal_right__"]`.

The docstring acknowledges this is interim until §3.8b. Two observations:
- Standard ROS2 trajectory controllers (controller_manager, MoveIt!) bound to this action name would interpret the goal as a joint-space trajectory and emit dangerous motion if anything else publishes there.
- Custom action types do **not** require a `colcon build` if the action server runs in the same Python process and the only clients are also Python (rclpy generates them at runtime). The justification in the docstring ("avoid a colcon build step for custom action types in Phase 3 spike") doesn't strictly hold — but the simpler argument is that the spec calls for `goal_pose_left + goal_pose_right` in `geometry_msgs/Pose`, which a custom `BimanualPlanMotion.action` would carry naturally.

**Suggested next step:** scope and merge §3.8b now rather than later; the workaround creates a foot-gun if any standard ROS2 component attaches to `/bimanual/plan_motion`.

---

### F-6 (Minor) — Feedback contract, cancel handling, malformed-worker handling

- **Feedback (spec mismatch):** docstring says "Feedback: progress 0.0–1.0 during IK solve." Implementation publishes feedback once with `fb.desired = points[0]` (lines 96-98) then blocks on `urlopen(req, timeout=30)`. No incremental progress.
- **Cancel:** `_cancel_cb` returns `ACCEPT`, but `_execute` never checks `goal_handle.is_cancel_requested` during the urlopen call. A cancel issued mid-solve is silently dropped until the 30 s timeout.
- **Worker success-but-malformed:** lines 109-114 read `resp["solve_ms"]`, `resp["joints"]`, `resp["trajectory"]` without checking presence. If worker returns `{"success": true}` with any missing field, the server raises an unhandled `KeyError` inside the executor — depending on rclpy version this can leak the goal handle.

---

## Verification harness

`scripts/verify_step_3_8a.py` (this repo):

```
usage: verify_step_3_8a.py [--mjcf URDF/PATH] (--fixture PATH | --synthetic) [--seed N] [--json]
```

- Pure dependencies: `mujoco`, `numpy`. No cuRobo / ROS2.
- Replays a worker-format JSON (`{"trajectory": [[14], ...], "joints": [...], ...}`).
- Gates: (A) joint-limit violation rate `< 0.1%` per Phase 3 S3 gate; (B) FK end-pose vs target (skipped without target poses); (C) self-collision per-waypoint, filtered through cuRobo's `self_collision_ignore`; (D) peak jerk `≤ 500 rad/s³` per yaml limit.
- Exits 0 on overall pass, 1 on any fail. Suitable for CI gating.
- Smoke run (synthetic, seed 0): A PASS, B SKIPPED, **C FAIL (60/60 frames, finding F-4)**, D PASS.

Live-fixture mode: capture worker output as JSON and pass via `--fixture` (with optional `_targets: {left: [...], right: [...]}` to enable gate B). The harness does not require cuRobo or ROS2 on the host — it is a pure-measurement vantage independent of Aegis's Isaac Sim stack.

---

## Out-of-scope (deferred to Aegis / Recon)

- IK solve-time targets (`< 50 ms`) — needs a live cuRobo run.
- ROS2 action client compliance from `view_robot_webrtc.py` — covered by §3.8b spec.
- OMX-F handoff trajectory (§3.8d) — not yet implemented anywhere.

---

## Plan-document sync

Plan §4 still lists Step 3.8 and 3.8a as `[PENDING]` although code landed in commit `51d6f87`. Suggest Aegis update `PHASE3_ROBOT_MOTION_PLAN_20260514.md` §3.8a to `[COMPLETED: 51d6f87]` **with footnote** referencing F-2 / F-3 (architectural deviation + collision-config gap) so future readers can find the gap.

---

*Filed by Moojoco per the "cross-verification citizen" seat framing from EOS, 2026-05-29 KST.*
