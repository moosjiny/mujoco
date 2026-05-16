from gymnasium.envs.registration import register

register(
    id="gym_dual_arms/DualArms-v0",
    entry_point="gym_dual_arms.envs:DualArmsEnv",
    max_episode_steps=1000,
)
