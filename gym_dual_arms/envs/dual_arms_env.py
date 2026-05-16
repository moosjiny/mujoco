"""
LeRobot-compatible gymnasium environment for the dual-arm MuJoCo digital twin.

Robots (all 3 in one model):
  - Bimanual OpenArm   : 7+2 left, 7+2 right  (16 actuators)
  - OMX-F follower arm : 5 DOF + 2 gripper     (7 actuators)
  - Vic Pinky base     : freejoint + 2 wheels  (2 actuators)
  Total: 25 actuators

Default cameras (defined in build_mjcf.py section 5b):
  - "overview"    : top-down, 3개 로봇 전체 확인
  - "front_right" : 우전방 사얼보기

Usage:
    import gymnasium as gym
    import gym_dual_arms  # registers env

    env = gym.make(
        "gym_dual_arms/DualArms-v0",
        obs_type="pixels_agent_pos",
        cameras=["overview", "front_right"],
        render_mode="rgb_array",
    )
    obs, info = env.reset()
    # obs keys: "observation.state", "observation.images.overview", ...

LeRobot dataset recording:
    from lerobot.common.datasets.lerobot_dataset import LeRobotDataset
    # env 리셋 후 step() 레코딩 시 observation.images.* 자동 밝히짐
"""
from __future__ import annotations

import os
from typing import Any

import mujoco
import numpy as np
import gymnasium as gym
from gymnasium import spaces

_DEFAULT_MODEL = os.environ.get(
    "DUAL_ARMS_MODEL",
    "/home/moos/dev_ws/dual_arms/urdf/dual_openarm.xml",
)

# qpos 레이아웃 (nq=34)
#   [0:18]   bimanual: left arm(7) + left fingers(2) + right arm(7) + right fingers(2)
#   [18:25]  omxf: joints 1-5 + 2 grippers
#   [25:32]  pinky_base_free: xyz + quat(wxyz)
#   [32:34]  pinky wheels: left, right
QPOS_BIMANUAL = slice(0,  18)
QPOS_OMXF     = slice(18, 25)
QPOS_PINKY    = slice(25, 34)


class DualArmsEnv(gym.Env):
    """Gymnasium environment wrapping the 3-robot MuJoCo dual-arm digital twin."""

    metadata = {"render_modes": ["rgb_array"], "render_fps": 30}

    def __init__(
        self,
        obs_type: str = "pixels_agent_pos",
        cameras: list[str] | None = None,
        img_width: int = 640,
        img_height: int = 480,
        render_mode: str | None = None,
        n_substeps: int = 5,
        model_path: str = _DEFAULT_MODEL,
    ):
        """
        Args:
            obs_type: "pixels" | "agent_pos" | "pixels_agent_pos"
            cameras:  list of camera names defined in the MJCF (default: ["overview"])
            img_width/img_height: rendered image size
            render_mode: gymnasium render mode ("rgb_array" for LeRobot)
            n_substeps: MuJoCo steps per env.step() (1 ms * 5 = 5 ms per action)
            model_path: path to dual_openarm.xml (override via DUAL_ARMS_MODEL env var)
        """
        super().__init__()
        if obs_type not in ("pixels", "agent_pos", "pixels_agent_pos"):
            raise ValueError(f"Unknown obs_type: {obs_type!r}")

        self.obs_type   = obs_type
        self.cameras    = cameras or ["overview"]
        self.img_width  = img_width
        self.img_height = img_height
        self.render_mode = render_mode
        self.n_substeps  = n_substeps

        self._model = mujoco.MjModel.from_xml_path(model_path)
        self._data  = mujoco.MjData(self._model)
        self._renderers: dict[str, mujoco.Renderer] = {}

        # Action space: all 25 actuators, bounded by model ctrlrange
        lo = self._model.actuator_ctrlrange[:, 0].copy()
        hi = self._model.actuator_ctrlrange[:, 1].copy()
        self.action_space = spaces.Box(low=lo, high=hi, dtype=np.float32)

        # Observation space
        obs_spaces: dict[str, spaces.Space] = {}
        if obs_type in ("agent_pos", "pixels_agent_pos"):
            # Full state: qpos (34) + qvel (33) — covers all 3 robots
            n = self._model.nq + self._model.nv
            obs_spaces["observation.state"] = spaces.Box(
                low=-np.inf, high=np.inf, shape=(n,), dtype=np.float32
            )
        if obs_type in ("pixels", "pixels_agent_pos"):
            for cam in self.cameras:
                obs_spaces[f"observation.images.{cam}"] = spaces.Box(
                    low=0, high=255,
                    shape=(img_height, img_width, 3),
                    dtype=np.uint8,
                )
        self.observation_space = spaces.Dict(obs_spaces)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_renderer(self, cam: str) -> mujoco.Renderer:
        if cam not in self._renderers:
            self._renderers[cam] = mujoco.Renderer(
                self._model, self.img_height, self.img_width
            )
        return self._renderers[cam]

    def _render_camera(self, cam: str) -> np.ndarray:
        r = self._get_renderer(cam)
        r.update_scene(self._data, camera=cam)
        return r.render()

    def _reset_state(self) -> None:
        mujoco.mj_resetData(self._model, self._data)
        # freejoint quat 수동 복원 (0-력 초기화하면 quaternion=(0,0,0,0) 무효)
        pinky_jnt = mujoco.mj_name2id(
            self._model, mujoco.mjtObj.mjOBJ_JOINT, "pinky_base_free"
        )
        if pinky_jnt >= 0:
            adr = self._model.jnt_qposadr[pinky_jnt]
            self._data.qpos[adr:adr + 3] = [0.0, 1.2, 0.0]   # vicpinky 시작 위치
            self._data.qpos[adr + 3:adr + 7] = [1.0, 0.0, 0.0, 0.0]  # identity quat
        mujoco.mj_forward(self._model, self._data)

    def _get_obs(self) -> dict[str, np.ndarray]:
        obs: dict[str, np.ndarray] = {}
        if self.obs_type in ("agent_pos", "pixels_agent_pos"):
            obs["observation.state"] = np.concatenate(
                [self._data.qpos, self._data.qvel]
            ).astype(np.float32)
        if self.obs_type in ("pixels", "pixels_agent_pos"):
            for cam in self.cameras:
                obs[f"observation.images.{cam}"] = self._render_camera(cam)
        return obs

    # ------------------------------------------------------------------
    # gymnasium API
    # ------------------------------------------------------------------

    def reset(
        self, *, seed: int | None = None, options: dict | None = None
    ) -> tuple[dict, dict]:
        super().reset(seed=seed)
        self._reset_state()
        return self._get_obs(), {}

    def step(
        self, action: np.ndarray
    ) -> tuple[dict, float, bool, bool, dict]:
        np.copyto(self._data.ctrl, action)
        for _ in range(self.n_substeps):
            mujoco.mj_step(self._model, self._data)
        obs = self._get_obs()
        return obs, 0.0, False, False, {}

    def render(self) -> np.ndarray | None:
        if self.render_mode == "rgb_array":
            return self._render_camera(self.cameras[0])
        return None

    def close(self) -> None:
        for r in self._renderers.values():
            r.close()
        self._renderers.clear()

    # ------------------------------------------------------------------
    # Convenience: per-robot state slices
    # ------------------------------------------------------------------

    @property
    def state_bimanual(self) -> np.ndarray:
        """Left + right OpenArm qpos (18 values)."""
        return self._data.qpos[QPOS_BIMANUAL].copy()

    @property
    def state_omxf(self) -> np.ndarray:
        """OMX-F arm qpos (7 values: 5 joints + 2 grippers)."""
        return self._data.qpos[QPOS_OMXF].copy()

    @property
    def state_pinky(self) -> np.ndarray:
        """Vic Pinky qpos (9 values: xyz + quat + 2 wheels)."""
        return self._data.qpos[QPOS_PINKY].copy()
