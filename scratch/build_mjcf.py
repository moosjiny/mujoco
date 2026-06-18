"""
Build dual_openarm.xml — single source of truth for the bimanual MuJoCo model.

Composition:
  * OpenArm bimanual chassis  -> loaded from urdf/dual_openarm.urdf
                                 (URDF already carries STL meshes + damping/friction)
  * OMX-F follower arm        -> built programmatically here, references the system
                                 STL meshes shipped by ros-jazzy-open-manipulator-description.
                                 The URDF (urdf/omx_f.urdf) is NOT used; its mesh paths
                                 point at a non-existent /home/addinedu/... tree.
  * vicpinky mobile base      -> built programmatically. urdf/vicpinky.urdf only has a
                                 chassis box + 2 wheels; the real chassis (top plate,
                                 4 aluminum pillars, casters, LiDAR mount) lives here.
  * Environment               -> headlight, skybox, checker ground, sun light.
  * Cameras                   -> overview (top-down) + front_right (angled): both capture
                                 all 3 robots in one frame for LeRobot gym rendering.

If you tweak OMX-F joint origins or vicpinky geometry, do it here — regenerating then
overwrites urdf/dual_openarm.xml exactly. Visual no-op for everything else.
"""
import mujoco

# Paths
OPENARM_URDF = "/home/moos/dev_ws/dual_arms/urdf/dual_openarm.urdf"
OUT          = "/home/moos/dev_ws/dual_arms/urdf/dual_openarm.xml"

OMXF_MESH_DIR = "/opt/ros/jazzy/share/open_manipulator_description/meshes/omx_f"
OMXF_MESH_FILES = [
    "follower_01_base.stl",
    "follower_02_base_tilt_Revised.stl",
    "follower_03_middle_verticle.stl",
    "follower_04_middle_horizontal.stl",
    "follower_05_tip.stl",
    "follower_06_pan_Revised.stl",
    "follower_07_gripper_motorized.stl",
    "follower_08_gripper_gear.stl",
]

VICPINKY_LIDAR_MESH = "/home/moos/dev_ws/dual_arms/meshes/vicpinky/lidar.stl"

# OMX-F constants
OMXF_RANGE     = [-3.14159, 3.14159]
OMXF_DAMPING   = [0.3, 0, 0]   # damping is a 3-element ndarray in MjSpec API
OMXF_FRICTION  = 0.02
OMXF_ARMATURE  = 0.001
OMXF_RGBA      = [0.2, 0.2, 0.2, 1]

# (link_name, body_pos_relative_to_parent, joint_name_or_None, joint_axis_or_None)
OMXF_SERIAL = [
    ("omxf_link0", [0,        0,  0       ], None,            None      ),
    ("omxf_link1", [0.01125,  0,  0.034   ], "omxf_joint1",   [0, 0, 1] ),
    ("omxf_link2", [0,        0,  0.0635  ], "omxf_joint2",   [0, 1, 0] ),
    ("omxf_link3", [0.0415,   0,  0.11315 ], "omxf_joint3",   [0, 1, 0] ),
    ("omxf_link4", [0.162,    0,  0       ], "omxf_joint4",   [0, 1, 0] ),
    ("omxf_link5", [0.0287,   0,  0       ], "omxf_joint5",   [1, 0, 0] ),
]
OMXF_GRIPPERS = [  # both attach under link5
    ("omxf_link6", [0.0295,  0.0075, 0], "omxf_gripper_joint_1", [0, 0, 1]),
    ("omxf_link7", [0.0295, -0.0108, 0], "omxf_gripper_joint_2", [0, 0, 1]),
]
OMXF_EE_OFFSET = [0.09193, -0.0016, 0]

# OpenArm actuators (URDF doesn't define them, so we add them by joint name)
OPENARM_ACTUATORS = [
    ("left_joint1_ctrl",   "left_joint_1",        -10,   10),
    ("left_joint2_ctrl",   "left_joint_2",        -12,   12),
    ("left_joint3_ctrl",   "left_joint_3",        -10,   10),
    ("left_joint4_ctrl",   "left_joint_4",        -10,   10),
    ("left_joint5_ctrl",   "left_joint_5",        -10,   10),
    ("left_joint6_ctrl",   "left_joint_6",        -10,   10),
    ("left_joint7_ctrl",   "left_joint_7",        -10,   10),
    ("left_finger_ctrl",   "left_finger_joint1",  -0.1,  0.1),
    ("right_joint1_ctrl",  "right_joint_1",       -10,   10),
    ("right_joint2_ctrl",  "right_joint_2",       -12,   12),
    ("right_joint3_ctrl",  "right_joint_3",       -10,   10),
    ("right_joint4_ctrl",  "right_joint_4",       -10,   10),
    ("right_joint5_ctrl",  "right_joint_5",       -10,   10),
    ("right_joint6_ctrl",  "right_joint_6",       -10,   10),
    ("right_joint7_ctrl",  "right_joint_7",       -10,   10),
    ("right_finger_ctrl",  "right_finger_joint1", -0.1,  0.1),
]


def add_position_actuator(spec, name, joint, kp, lo, hi):
    a = spec.add_actuator()
    a.name = name
    a.target = joint
    a.trntype = mujoco.mjtTrn.mjTRN_JOINT
    a.gaintype = mujoco.mjtGain.mjGAIN_FIXED
    a.biastype = mujoco.mjtBias.mjBIAS_AFFINE
    a.gainprm = [float(kp)] + [0.0] * 9
    a.biasprm = [0.0, -float(kp)] + [0.0] * 8
    a.ctrlrange = [lo, hi]
    a.ctrllimited = 1


def add_velocity_actuator(spec, name, joint, kv, lo, hi):
    a = spec.add_actuator()
    a.name = name
    a.target = joint
    a.trntype = mujoco.mjtTrn.mjTRN_JOINT
    a.gaintype = mujoco.mjtGain.mjGAIN_FIXED
    a.biastype = mujoco.mjtBias.mjBIAS_AFFINE
    # <velocity kv=K> ⇔ gain K, bias[2] = -K (proportional to velocity)
    a.gainprm = [float(kv)] + [0.0] * 9
    a.biasprm = [0.0, 0.0, -float(kv)] + [0.0] * 7
    a.ctrlrange = [lo, hi]
    a.ctrllimited = 1


# ---------- 1. Base spec from OpenArm URDF ----------
spec = mujoco.MjSpec.from_file(OPENARM_URDF)
spec.option.timestep = 0.001
spec.option.integrator = mujoco.mjtIntegrator.mjINT_IMPLICITFAST


def enable_collisions(body):
    # URDF-loaded geoms come out with contype=0/conaffinity=0; flip them to MuJoCo's
    # native default (1/1) so the arms actually collide.
    for geom in body.geoms:
        geom.contype = 1
        geom.conaffinity = 1
    for child in body.bodies:
        enable_collisions(child)


enable_collisions(spec.worldbody)

# ---------- 2. Visual ----------
spec.visual.headlight.ambient  = [0.4, 0.4, 0.4]
spec.visual.headlight.diffuse  = [0.6, 0.6, 0.6]
spec.visual.headlight.specular = [0.2, 0.2, 0.2]
spec.visual.global_.offwidth   = 1920
spec.visual.global_.offheight  = 1080

# ---------- 3. Sky / ground textures + material ----------
sky = spec.add_texture()
sky.type    = mujoco.mjtTexture.mjTEXTURE_SKYBOX
sky.builtin = mujoco.mjtBuiltin.mjBUILTIN_GRADIENT
sky.rgb1    = [0.55, 0.70, 0.85]
sky.rgb2    = [0.10, 0.15, 0.25]
sky.width   = 512
sky.height  = 3072

gp_tex = spec.add_texture()
gp_tex.name    = "groundplane"
gp_tex.type    = mujoco.mjtTexture.mjTEXTURE_2D
gp_tex.builtin = mujoco.mjtBuiltin.mjBUILTIN_CHECKER
gp_tex.mark    = mujoco.mjtMark.mjMARK_EDGE
gp_tex.rgb1    = [0.25, 0.30, 0.35]
gp_tex.rgb2    = [0.18, 0.22, 0.27]
gp_tex.markrgb = [0.7, 0.7, 0.7]
gp_tex.width   = 512
gp_tex.height  = 512

gp_mat = spec.add_material()
gp_mat.name        = "groundplane"
gp_mat.textures[mujoco.mjtTextureRole.mjTEXROLE_RGB] = "groundplane"
gp_mat.texuniform  = True
gp_mat.texrepeat   = [6, 6]
gp_mat.reflectance = 0.15

# ---------- 4. Mesh assets ----------
for i, fname in enumerate(OMXF_MESH_FILES):
    m = spec.add_mesh()
    m.name  = f"omxf_link{i}_mesh"
    m.file  = f"{OMXF_MESH_DIR}/{fname}"
    m.scale = [0.001, 0.001, 0.001]

lidar_mesh = spec.add_mesh()
lidar_mesh.name  = "vicpinky_lidar_mesh"
lidar_mesh.file  = VICPINKY_LIDAR_MESH
lidar_mesh.scale = [1, 1, 1]

# ---------- 5. Floor + sun ----------
floor = spec.worldbody.add_geom()
floor.name     = "floor"
floor.type     = mujoco.mjtGeom.mjGEOM_PLANE
floor.size     = [0, 0, 0.05]
floor.pos      = [0, 0.5, -0.05]
floor.material = "groundplane"

sun = spec.worldbody.add_light()
sun.name       = "sun"
sun.type       = mujoco.mjtLightType.mjLIGHT_DIRECTIONAL
sun.pos        = [2, -2, 5]
sun.dir        = [-0.3, 0.3, -1]
sun.diffuse    = [0.7, 0.7, 0.65]
sun.specular   = [0.2, 0.2, 0.2]
sun.castshadow = True

# ---------- 5b. Scene cameras (3개 로봇 모두 시야에) ----------
# 쌍 배치:
#   양팔 OpenArm  : origin (0, 0, 0)
#   OMX-F stand: (0.6, -0.3, 0.8)
#   vicpinky   : (0, 1.2, 0)
#   사실상 중심 : (0.2, 0.3, 0.5)

# overview: 수직 하강 탑뷰. xyaxes=[x=우, y=앞] → 카메라 z=위 → -z=아래 직시
_cam_ov = spec.worldbody.add_camera()
_cam_ov.name   = "overview"
_cam_ov.pos    = [0.2, 0.3, 4.5]
_cam_ov.xyaxes = [1, 0, 0, 0, 1, 0]
_cam_ov.fovy   = 70

# front_right: 우전방 사얼었기. zaxis = cam_pos - lookat (날고 있는 방향의 반대)
# lookat=(0.2, 0.3, 0.5), pos=(2.5, -2.0, 1.8)
# zaxis_raw=(2.3, -2.3, 1.3), |v|=3.503, normalized=(0.657, -0.657, 0.371)
_cam_fr = spec.worldbody.add_camera()
_cam_fr.name  = "front_right"
_cam_fr.pos   = [2.5, -2.0, 1.8]
_cam_fr.zaxis = [0.657, -0.657, 0.371]
_cam_fr.fovy  = 55

# ---------- 6. OMX-F body tree ----------
omxf_stand = spec.worldbody.add_body()
omxf_stand.name = "omxf_stand"
omxf_stand.pos  = [0.6, -0.3, 0]
g = omxf_stand.add_geom()
g.type = mujoco.mjtGeom.mjGEOM_BOX
g.size = [0.1, 0.1, 0.4]
g.pos  = [0, 0, 0.4]
g.rgba = [0.3, 0.3, 0.3, 1]

omxf_root = omxf_stand.add_body()
omxf_root.name = "omxf_root"
omxf_root.pos  = [0, 0, 0.8]

parent = omxf_root
for i, (lname, lpos, jname, jaxis) in enumerate(OMXF_SERIAL):
    b = parent.add_body()
    b.name = lname
    b.pos  = lpos
    if jname is not None:
        j = b.add_joint()
        j.name         = jname
        j.axis         = jaxis
        j.range        = OMXF_RANGE
        j.damping      = OMXF_DAMPING
        j.frictionloss = OMXF_FRICTION
        j.armature     = OMXF_ARMATURE
    g = b.add_geom()
    g.type     = mujoco.mjtGeom.mjGEOM_MESH
    g.meshname = f"omxf_link{i}_mesh"
    g.rgba     = OMXF_RGBA
    parent = b

# Grippers (link6, link7) hang off link5 in parallel
link5 = parent
for idx, (lname, lpos, jname, jaxis) in enumerate(OMXF_GRIPPERS, start=6):
    b = link5.add_body()
    b.name = lname
    b.pos  = lpos
    j = b.add_joint()
    j.name         = jname
    j.axis         = jaxis
    j.range        = OMXF_RANGE
    j.damping      = OMXF_DAMPING
    j.frictionloss = OMXF_FRICTION
    j.armature     = OMXF_ARMATURE
    g = b.add_geom()
    g.type     = mujoco.mjtGeom.mjGEOM_MESH
    g.meshname = f"omxf_link{idx}_mesh"
    g.rgba     = OMXF_RGBA

ee = link5.add_body()
ee.name = "omxf_end_effector_link"
ee.pos  = OMXF_EE_OFFSET

# ---------- 6b. IK mocap targets ----------
# sim_ros2_ik.py looks these up by name and drives them via RViz interactive markers
# (/target_{left,right}/pose_cmd). contype=2/conaffinity=0 keeps them visible but
# non-colliding with the arms.
for tname, tpos, trgba in [
    ("target_left",  [0, -0.541, 0.773], [1, 0, 0, 0.5]),
    ("target_right", [0,  0.541, 0.773], [0, 0, 1, 0.5]),
]:
    tb = spec.worldbody.add_body()
    tb.name  = tname
    tb.pos   = tpos
    tb.mocap = True
    tg = tb.add_geom()
    tg.type        = mujoco.mjtGeom.mjGEOM_SPHERE
    tg.size        = [0.08, 0, 0]
    tg.contype     = 2
    tg.conaffinity = 0
    tg.rgba        = trgba

# ---------- 7. Vicpinky body tree ----------
pinky_base = spec.worldbody.add_body()
pinky_base.name = "pinky_base"
pinky_base.pos  = [0, 1.2, 0]
fj = pinky_base.add_freejoint()
fj.name = "pinky_base_free"
pinky_base.ipos    = [-0.2, 0, 0.08]
pinky_base.mass    = 15
pinky_base.inertia = [0.4, 0.6, 0.8]
pinky_base.explicitinertial = True

pfoot = pinky_base.add_body()
pfoot.name = "pinky_base_footprint"

plink = pfoot.add_body()
plink.name = "pinky_base_link"
plink.pos  = [0, 0, 0.0325]

# Chassis + plate + pillars (boxes)
CHASSIS_BOXES = [
    ("pinky_chassis",   [0.3,   0.2,   0.07 ], [-0.2,    0,     0.05]),
    ("pinky_top_plate", [0.3,   0.2,   0.015], [-0.2,    0,     0.6 ]),
    ("pinky_pillar_fl", [0.015, 0.015, 0.25 ], [ 0.085,  0.185, 0.37]),
    ("pinky_pillar_fr", [0.015, 0.015, 0.25 ], [ 0.085, -0.185, 0.37]),
    ("pinky_pillar_rl", [0.015, 0.015, 0.25 ], [-0.485,  0.185, 0.37]),
    ("pinky_pillar_rr", [0.015, 0.015, 0.25 ], [-0.485, -0.185, 0.37]),
]
for name, size, pos in CHASSIS_BOXES:
    g = plink.add_geom()
    g.name = name
    g.type = mujoco.mjtGeom.mjGEOM_BOX
    g.size = size
    g.pos  = pos
    g.rgba = [0.2, 0.2, 0.2, 1]

# Casters (spheres with low friction so they slide)
for name, pos in [("pinky_caster_l", [-0.4,  0.1, -0.05]),
                  ("pinky_caster_r", [-0.4, -0.1, -0.05])]:
    g = plink.add_geom()
    g.name     = name
    g.type     = mujoco.mjtGeom.mjGEOM_SPHERE
    g.size     = [0.0325, 0, 0]
    g.pos      = pos
    g.rgba     = [0.2, 0.2, 0.2, 1]
    g.friction = [0.05, 0.001, 0.0001]

# LiDAR mount
lidar = plink.add_body()
lidar.name = "pinky_lidar_mount"
lidar.pos  = [0, 0, 0.18]
g = lidar.add_geom()
g.name     = "pinky_lidar_mesh"
g.type     = mujoco.mjtGeom.mjGEOM_MESH
g.meshname = "vicpinky_lidar_mesh"
g.rgba     = [0, 0, 1, 1]
g = lidar.add_geom()
g.name = "pinky_lidar_box"
g.type = mujoco.mjtGeom.mjGEOM_BOX
g.size = [0.035, 0.035, 0.035]
g.pos  = [0, 0, -0.035]
g.rgba = [0, 0, 1, 1]

# Wheels
WHEELS = [
    ("pinky_left_wheel",  "pinky_left_wheel_joint",  [0,  0.2375, 0],
     [0.707109, -0.707105, 0, 0], [0, 0,  1]),
    ("pinky_right_wheel", "pinky_right_wheel_joint", [0, -0.2375, 0],
     [0.707109,  0.707105, 0, 0], [0, 0, -1]),
]
for bname, jname, pos, quat, axis in WHEELS:
    w = plink.add_body()
    w.name = bname
    w.pos  = pos
    w.quat = quat
    j = w.add_joint()
    j.name    = jname
    j.axis    = axis
    j.damping = [0.01, 0, 0]
    g = w.add_geom()
    g.type     = mujoco.mjtGeom.mjGEOM_CYLINDER
    g.size     = [0.0825, 0.025, 0]
    g.rgba     = [0, 0, 0, 1]
    g.friction = [2.0, 0.02, 0.001]

# ---------- 8. Actuators ----------
# OMX-F: position control, kp=100
for jname in ("omxf_joint1", "omxf_joint2", "omxf_joint3", "omxf_joint4",
              "omxf_joint5", "omxf_gripper_joint_1", "omxf_gripper_joint_2"):
    add_position_actuator(spec, f"{jname}_ctrl", jname, 100, *OMXF_RANGE)

# Pinky wheels: velocity control, kv=150
add_velocity_actuator(spec, "pinky_left_wheel_joint_ctrl",  "pinky_left_wheel_joint",  150, -10, 10)
add_velocity_actuator(spec, "pinky_right_wheel_joint_ctrl", "pinky_right_wheel_joint", 150, -10, 10)

# OpenArm: position control, kp=200 (50 for fingers)
for name, joint, lo, hi in OPENARM_ACTUATORS:
    kp = 50 if "finger" in name else 200
    add_position_actuator(spec, name, joint, kp, lo, hi)

# ---------- 9. Compile & save ----------
m = spec.compile()
xml_str = spec.to_xml()
with open(OUT, "w") as f:
    f.write(xml_str)

print(f"Saved merged model to {OUT}")
print(f"  njnt={m.njnt}  nu={m.nu}  nbody={m.nbody}  nmesh={m.nmesh}")
print(f"  cameras: {[m.camera(i).name for i in range(m.ncam)]}")
