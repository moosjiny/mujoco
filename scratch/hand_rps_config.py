"""
Rock-Paper-Scissors 목표 관절각 테이블 — 20-DOF 손 모델 (4 DOF/finger).

좌표계·부호 규칙 (사령관 제공 스펙, 2026-09-14):
  기준 자세(0.00 rad) = 손바닥 평면과 수평으로 곧게 편 완전 신전 상태
  Flexion (+)   : 손바닥 안쪽으로 굽힘
  Abduction (+) : 중지(Middle) 중심선 기준 바깥쪽으로 벌어짐
  Opposition(+) : 엄지가 손바닥 안쪽을 마주보도록 회전/대립

관절 정의:
  엄지(thumb)              : CMC_opp, CMC_abd, MCP_flex, IP_flex
  4지(index/middle/ring/pinky): MCP_abd, MCP_flex, PIP_flex, DIP_flex

모든 값은 라디안. degree 주석은 검산용(전부 rad*180/pi로 재계산해 원본과 일치 확인됨).
"""

import math

FINGERS = ("thumb", "index", "middle", "ring", "pinky")

THUMB_JOINTS = ("CMC_opp", "CMC_abd", "MCP_flex", "IP_flex")
FINGER_JOINTS = ("MCP_abd", "MCP_flex", "PIP_flex", "DIP_flex")

JOINT_NAMES = {
    "thumb": THUMB_JOINTS,
    "index": FINGER_JOINTS,
    "middle": FINGER_JOINTS,
    "ring": FINGER_JOINTS,
    "pinky": FINGER_JOINTS,
}

# gesture -> finger -> joint -> radian
GESTURES = {
    "rock": {
        "thumb":  {"CMC_opp": 0.75, "CMC_abd": -0.35, "MCP_flex": 0.90, "IP_flex": 0.80},
        "index":  {"MCP_abd": 0.00, "MCP_flex": 1.50, "PIP_flex": 1.65, "DIP_flex": 1.10},
        "middle": {"MCP_abd": 0.00, "MCP_flex": 1.55, "PIP_flex": 1.70, "DIP_flex": 1.10},
        "ring":   {"MCP_abd": 0.00, "MCP_flex": 1.55, "PIP_flex": 1.70, "DIP_flex": 1.10},
        "pinky":  {"MCP_abd": 0.00, "MCP_flex": 1.50, "PIP_flex": 1.65, "DIP_flex": 1.10},
    },
    "scissors": {
        "thumb":  {"CMC_opp": 0.90, "CMC_abd": -0.45, "MCP_flex": 1.05, "IP_flex": 0.90},
        "index":  {"MCP_abd": 0.25, "MCP_flex": 0.05, "PIP_flex": 0.00, "DIP_flex": 0.00},
        "middle": {"MCP_abd": -0.10, "MCP_flex": 0.05, "PIP_flex": 0.00, "DIP_flex": 0.00},
        "ring":   {"MCP_abd": 0.00, "MCP_flex": 1.55, "PIP_flex": 1.70, "DIP_flex": 1.10},
        "pinky":  {"MCP_abd": 0.00, "MCP_flex": 1.50, "PIP_flex": 1.65, "DIP_flex": 1.10},
    },
    "paper": {
        "thumb":  {"CMC_opp": 0.10, "CMC_abd": 0.75, "MCP_flex": 0.10, "IP_flex": 0.00},
        "index":  {"MCP_abd": 0.15, "MCP_flex": 0.00, "PIP_flex": 0.00, "DIP_flex": 0.00},
        "middle": {"MCP_abd": 0.00, "MCP_flex": 0.00, "PIP_flex": 0.00, "DIP_flex": 0.00},
        "ring":   {"MCP_abd": -0.08, "MCP_flex": 0.00, "PIP_flex": 0.00, "DIP_flex": 0.00},
        "pinky":  {"MCP_abd": -0.20, "MCP_flex": 0.00, "PIP_flex": 0.00, "DIP_flex": 0.00},
    },
}

# 상태 전이 시퀀스 — 데모/사용자 표시용 기본 3틱 순환. 무작위 발생 시 random.choice(list(GESTURES)) 사용 권장.
STATE_TRANSITION_SEQUENCE = ["rock", "paper", "scissors", "rock"]


def ordered_joint_names():
    """(finger, joint) 튜플을 실린더 순서(엄지→새끼, 각 지별 관절 4개)로 반환. MJCF/actuator 순서와 일치시키는 데 사용."""
    names = []
    for finger in FINGERS:
        for joint in JOINT_NAMES[finger]:
            names.append((finger, joint))
    return names


def target_vector(gesture: str):
    """gesture 이름 -> 20-길이 라디안 배열 (ordered_joint_names() 순서)."""
    if gesture not in GESTURES:
        raise ValueError(f"unknown gesture: {gesture!r}, expected one of {list(GESTURES)}")
    g = GESTURES[gesture]
    return [g[finger][joint] for finger, joint in ordered_joint_names()]


def mjcf_joint_id(finger: str, joint: str) -> str:
    """MJCF <joint name=...> 와 일치하는 문자열 식별자."""
    return f"{finger}_{joint}"


def _verify_degree_annotations():
    """원본 스펙에 병기된 도(degree) 주석과 rad*180/pi 재계산이 일치하는지 검산 (문서화용, 실행 시 assert)."""
    checks = [
        (0.75, 43), (0.90, 52), (0.80, 46), (1.50, 86), (1.65, 95),
        (1.10, 63), (1.55, 89), (1.70, 97), (1.05, 60), (0.25, 14),
        (0.05, 3), (0.10, 6), (0.15, 9),
    ]
    for rad, deg in checks:
        computed = round(math.degrees(rad))
        assert computed == deg, f"{rad} rad -> {computed}° (expected ~{deg}°)"


if __name__ == "__main__":
    _verify_degree_annotations()
    for name in GESTURES:
        vec = target_vector(name)
        print(f"{name:10s} n_joints={len(vec)} range=({min(vec):+.2f}, {max(vec):+.2f}) rad")
    print("degree 주석 검산: OK")
