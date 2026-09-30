"""
Build hand_rps.xml — 20-DOF 5지 손 모델 (SINGLE SOURCE OF TRUTH).

가위바위보 관절각 테이블(hand_rps_config.py)을 실행하기 위한 전용 손 모델.
기존 dual_openarm의 평행 그리퍼(finger_joint1 1-DOF)와는 별개의 독립 자산 —
build_mjcf.py가 만드는 팔 모델에 얹는 것이 아니라 단독 시뮬레이션용.

기구학:
  손바닥(palm) 고정 바디 위에 5개 손가락 체인을 부착.
  엄지: CMC_opp(대립) -> CMC_abd(외전) -> MCP_flex -> IP_flex   (4 hinge)
  4지 : MCP_abd(외전) -> MCP_flex -> PIP_flex -> DIP_flex        (4 hinge)
  각 세그먼트는 capsule 지오메트리로 시각화, 링크 길이는 성인 평균 손가락
  분절 비율(근위:중위:원위 ≈ 2:1.2:1)을 단순화해 적용.

재생성:
  python3 scratch/build_hand_mjcf.py
  -> urdf/hand_rps.xml 로 저장 (dual_openarm.xml과 동일 디렉토리 관례 유지)
"""
import mujoco

OUT = "/home/user/mujoco/urdf/hand_rps.xml"

# 손가락별 분절 길이 (m) — [근위(MCP-PIP 또는 CMC-MCP), 중위(PIP-DIP), 원위(DIP-tip)]
FINGER_LEN = {
    "thumb":  (0.045, 0.030, 0.025),
    "index":  (0.045, 0.028, 0.020),
    "middle": (0.050, 0.030, 0.022),
    "ring":   (0.046, 0.028, 0.020),
    "pinky":  (0.038, 0.022, 0.018),
}

# 손바닥 위 각 손가락 부착 원점 (palm frame, x=요골쪽/엄지쪽 +, y=원위 방향 +, z=배측 +)
FINGER_ORIGIN = {
    "thumb":  (-0.035, 0.010, 0.010),
    "index":  (-0.028, 0.085, 0.000),
    "middle": (-0.008, 0.090, 0.000),
    "ring":   (0.014, 0.086, 0.000),
    "pinky":  (0.034, 0.078, 0.000),
}

RADIUS = 0.008  # capsule 반지름 (성인 손가락 굵기 근사)

JOINT_LIMITS = {
    # (finger, joint) -> (lo, hi) rad — Unitree Dex5-1 실측 URDF 관절 한계각 그대로 적용.
    # 출처: unitreerobotics/unitree_ros, robots/dexterous_hand_description/dex5_1/
    #       Dex5-URDF-L/Dex5-URDF-L.urdf (2026-09-23 raw fetch로 원문 확인)
    #       Yaw_11L/Roll_12L/Pitch_13L/Pitch_14L(엄지), Roll_x1L/Pitch_x2L/Pitch_x3L/Pitch_x4L(4지)
    # 조사 기록: thesis 2026-09-23-mojo-unitree-dex-hand-lineup-handshake-relevance
    ("thumb", "CMC_opp"):  (-0.587, 0.680),   # Yaw_11L
    ("thumb", "CMC_abd"):  (-1.815, 0.000),   # Roll_12L — 원 스펙과 부호 관례가 반대(주 4 참조)
    ("thumb", "MCP_flex"): (0.000, 1.765),    # Pitch_13L
    ("thumb", "IP_flex"):  (0.000, 1.641),    # Pitch_14L
    ("index", "MCP_abd"):  (-0.384, 0.384),   # Roll_21L
    ("index", "MCP_flex"): (0.000, 1.571),    # Pitch_22L
    ("index", "PIP_flex"): (0.000, 1.684),    # Pitch_23L
    ("index", "DIP_flex"): (0.000, 1.396),    # Pitch_24L
    ("middle", "MCP_abd"): (-0.384, 0.384),   # Roll_31L
    ("middle", "MCP_flex"): (0.000, 1.571),   # Pitch_32L
    ("middle", "PIP_flex"): (0.000, 1.684),   # Pitch_33L
    ("middle", "DIP_flex"): (0.000, 1.396),   # Pitch_34L
    ("ring", "MCP_abd"):   (-0.384, 0.384),   # (Link_)41L — 실제 URDF에도 조인트명 오기 존재
    ("ring", "MCP_flex"):  (0.000, 1.571),    # Pitch_42L
    ("ring", "PIP_flex"):  (0.000, 1.684),    # Pitch_43L
    ("ring", "DIP_flex"):  (0.000, 1.396),    # Pitch_44L
    ("pinky", "MCP_abd"):  (-0.384, 0.384),   # Roll_51L
    ("pinky", "MCP_flex"): (0.000, 1.571),    # Pitch_52L
    ("pinky", "PIP_flex"): (0.000, 1.684),    # Pitch_53L
    ("pinky", "DIP_flex"): (0.000, 1.396),     # Pitch_54L
}


def thumb_body_xml(parent, origin):
    lens = FINGER_LEN["thumb"]
    # CMC_opp (대립: 손바닥 법선 축 회전) 후 CMC_abd (외전: z축) 후 MCP_flex, IP_flex (x축, 굴곡)
    b0 = parent.add_body(name="thumb_cmc", pos=origin)
    b0.add_joint(name="thumb_CMC_opp", type=mujoco.mjtJoint.mjJNT_HINGE,
                 axis=[0, 1, 0], pos=[0, 0, 0],
                 range=JOINT_LIMITS[("thumb", "CMC_opp")])
    b0.add_geom(type=mujoco.mjtGeom.mjGEOM_SPHERE, size=[RADIUS * 0.6, 0, 0],
                rgba=[0.85, 0.7, 0.6, 1])
    b1 = b0.add_body(name="thumb_cmc_abd", pos=[0, 0, 0])
    b1.add_joint(name="thumb_CMC_abd", type=mujoco.mjtJoint.mjJNT_HINGE,
                 axis=[0, 0, 1], pos=[0, 0, 0],
                 range=JOINT_LIMITS[("thumb", "CMC_abd")])
    b1.add_geom(type=mujoco.mjtGeom.mjGEOM_CAPSULE, size=[RADIUS, lens[0] / 2],
                fromto=[0, 0, 0, 0, lens[0], 0], rgba=[0.85, 0.7, 0.6, 1])
    b2 = b1.add_body(name="thumb_mcp", pos=[0, lens[0], 0])
    b2.add_joint(name="thumb_MCP_flex", type=mujoco.mjtJoint.mjJNT_HINGE,
                 axis=[1, 0, 0], pos=[0, 0, 0],
                 range=JOINT_LIMITS[("thumb", "MCP_flex")])
    b2.add_geom(type=mujoco.mjtGeom.mjGEOM_CAPSULE, size=[RADIUS * 0.9, lens[1] / 2],
                fromto=[0, 0, 0, 0, lens[1], 0], rgba=[0.85, 0.7, 0.6, 1])
    b3 = b2.add_body(name="thumb_ip", pos=[0, lens[1], 0])
    b3.add_joint(name="thumb_IP_flex", type=mujoco.mjtJoint.mjJNT_HINGE,
                 axis=[1, 0, 0], pos=[0, 0, 0],
                 range=JOINT_LIMITS[("thumb", "IP_flex")])
    b3.add_geom(type=mujoco.mjtGeom.mjGEOM_CAPSULE, size=[RADIUS * 0.8, lens[2] / 2],
                fromto=[0, 0, 0, 0, lens[2], 0], rgba=[0.9, 0.75, 0.65, 1])
    b3.add_site(name="thumb_tip", pos=[0, lens[2], 0], size=[0.004])


def finger_body_xml(parent, finger, origin):
    lens = FINGER_LEN[finger]
    b0 = parent.add_body(name=f"{finger}_mcp_abd", pos=origin)
    b0.add_joint(name=f"{finger}_MCP_abd", type=mujoco.mjtJoint.mjJNT_HINGE,
                 axis=[0, 0, 1], pos=[0, 0, 0],
                 range=JOINT_LIMITS[(finger, "MCP_abd")])
    b0.add_geom(type=mujoco.mjtGeom.mjGEOM_SPHERE, size=[RADIUS * 0.6, 0, 0],
                rgba=[0.85, 0.7, 0.6, 1])
    b1 = b0.add_body(name=f"{finger}_mcp", pos=[0, 0, 0])
    b1.add_joint(name=f"{finger}_MCP_flex", type=mujoco.mjtJoint.mjJNT_HINGE,
                 axis=[1, 0, 0], pos=[0, 0, 0],
                 range=JOINT_LIMITS[(finger, "MCP_flex")])
    b1.add_geom(type=mujoco.mjtGeom.mjGEOM_CAPSULE, size=[RADIUS, lens[0] / 2],
                fromto=[0, 0, 0, 0, lens[0], 0], rgba=[0.85, 0.7, 0.6, 1])
    b2 = b1.add_body(name=f"{finger}_pip", pos=[0, lens[0], 0])
    b2.add_joint(name=f"{finger}_PIP_flex", type=mujoco.mjtJoint.mjJNT_HINGE,
                 axis=[1, 0, 0], pos=[0, 0, 0],
                 range=JOINT_LIMITS[(finger, "PIP_flex")])
    b2.add_geom(type=mujoco.mjtGeom.mjGEOM_CAPSULE, size=[RADIUS * 0.85, lens[1] / 2],
                fromto=[0, 0, 0, 0, lens[1], 0], rgba=[0.85, 0.7, 0.6, 1])
    b3 = b2.add_body(name=f"{finger}_dip", pos=[0, lens[1], 0])
    b3.add_joint(name=f"{finger}_DIP_flex", type=mujoco.mjtJoint.mjJNT_HINGE,
                 axis=[1, 0, 0], pos=[0, 0, 0],
                 range=JOINT_LIMITS[(finger, "DIP_flex")])
    b3.add_geom(type=mujoco.mjtGeom.mjGEOM_CAPSULE, size=[RADIUS * 0.75, lens[2] / 2],
                fromto=[0, 0, 0, 0, lens[2], 0], rgba=[0.9, 0.75, 0.65, 1])
    b3.add_site(name=f"{finger}_tip", pos=[0, lens[2], 0], size=[0.004])


def build():
    spec = mujoco.MjSpec()
    spec.compiler.degree = False
    spec.option.integrator = mujoco.mjtIntegrator.mjINT_IMPLICITFAST
    spec.option.timestep = 0.001

    spec.worldbody.add_light(pos=[0, 0, 1.5], type=mujoco.mjtLightType.mjLIGHT_DIRECTIONAL)
    spec.worldbody.add_geom(type=mujoco.mjtGeom.mjGEOM_PLANE, size=[1, 1, 0.1],
                             pos=[0, 0, -0.15], rgba=[0.3, 0.3, 0.32, 1])

    # 손목 위치 고정(world에 용접) — 목표는 finger 관절 추종 검증이지 자유낙하 동역학이 아님.
    # 실제 팔에 부착 시 이 body를 팔 손목 링크의 child로 재부모화(reparent)하면 된다.
    palm = spec.worldbody.add_body(name="palm", pos=[0, 0, 0.15])
    palm.add_geom(type=mujoco.mjtGeom.mjGEOM_BOX, size=[0.04, 0.05, 0.012],
                  rgba=[0.8, 0.65, 0.55, 1])

    thumb_body_xml(palm, FINGER_ORIGIN["thumb"])
    for finger in ("index", "middle", "ring", "pinky"):
        finger_body_xml(palm, finger, FINGER_ORIGIN[finger])

    # 자체 충돌(self-collision) 배제 — rock/scissors 자세에서 엄지가 검지·중지 위를
    # 덮을 때 손가락 캡슐끼리 물리적으로 부딪혀 저강성 위치 서보를 밀어내는 문제가
    # 실측(ncon>0, thumb_ip<->index_pip 등)으로 확인됨. 이 모델은 파지 접촉 물리를
    # 검증하는 용도가 아니라 목표각 추종/시각화가 목적이므로, 손 내부 body 쌍 전체를
    # 명시적으로 제외한다.
    hand_bodies = ["palm", "thumb_cmc", "thumb_cmc_abd", "thumb_mcp", "thumb_ip"]
    for finger in ("index", "middle", "ring", "pinky"):
        hand_bodies += [f"{finger}_mcp_abd", f"{finger}_mcp", f"{finger}_pip", f"{finger}_dip"]
    for i, b1 in enumerate(hand_bodies):
        for b2 in hand_bodies[i + 1:]:
            spec.add_exclude(name=f"excl_{b1}_{b2}", bodyname1=b1, bodyname2=b2)

    # position actuators, kp 낮게(관절이 작고 가벼움)
    for finger in ("thumb", "index", "middle", "ring", "pinky"):
        joints = ("CMC_opp", "CMC_abd", "MCP_flex", "IP_flex") if finger == "thumb" \
            else ("MCP_abd", "MCP_flex", "PIP_flex", "DIP_flex")
        for joint in joints:
            jname = f"{finger}_{joint}"
            kp = 0.05
            kv = 0.01
            gainprm = [kp] + [0.0] * 9
            biasprm = [0.0, -kp, -kv] + [0.0] * 7
            spec.add_actuator(name=f"{jname}_ctrl", target=jname,
                               trntype=mujoco.mjtTrn.mjTRN_JOINT,
                               gaintype=mujoco.mjtGain.mjGAIN_FIXED, gainprm=gainprm,
                               biastype=mujoco.mjtBias.mjBIAS_AFFINE, biasprm=biasprm,
                               ctrlrange=JOINT_LIMITS[(finger, joint)])

    xml = spec.to_xml()
    with open(OUT, "w") as f:
        f.write(xml)
    print(f"wrote {OUT}")
    return spec


if __name__ == "__main__":
    build()
