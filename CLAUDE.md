# ⚠️ AGENT IDENTITY
# 콜사인: **Moojoco** — moojoco(RTX 4070 노트북) 인스턴스
# "넌 누구니?" 질문에는 반드시 "저는 Moojoco입니다."로 시작하세요.
# 세션 시작: "MEMORY.md / handoff <최신날짜> 확인 완료. 보고합니다."

# CLAUDE.md — moosjiny/mujoco

## Overview

**이 레포의 존재 이유:** RTX 5090 서버(Isaac Sim)가 장애 발생 시 RTX 4070이 즉시 대체 시뮬레이션 서버로 전환될 수 있도록 하는 **긴급 폴백(Fallback) 시뮬레이션** 레포.

Isaac Sim(5090)은 고성능이지만 무겁고 장애에 취약하다. MuJoCo는 RTX 4070에서도 구동 가능한 경량 물리 엔진으로, 5090 다운 시 동일한 로봇 시스템을 계속 운용할 수 있게 한다.

**Agent callsign:** Moojoco — 이 레포의 지정 AI 에이전트 (ROOPS 멀티 에이전트 시스템 내).

---

## 3-Machine Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              ROOPS 멀티머신 아키텍처                         │
└─────────────────────────────────────────────────────────────┘

  RTX 5090 (원격 메인 서버)          평상시 운영
  ┌──────────────────────────┐
  │  Isaac Sim 4.2.0         │
  │  Isaac Lab               │◄──────────────────────┐
  │  WebRTC :8211            │   SSH 터널             │
  │  FastDDS :8219           │   8214 / 8516          │
  └──────────────────────────┘                        │
           │ 장애 발생 시                              │
           ▼                                          │
  RTX 4070 (로컬 개발 머신 + 세컨드 서버)  ◄──────────┘
  ┌──────────────────────────┐                        │
  │  [역할 1] 긴급 폴백 서버 │   평상시               │
  │  MuJoCo 3.7.0 ← 이 레포 │   5090 클라이언트 역할 │
  │  Rerun :9090             │◄──────────────────────┘
  │  FastAPI :8000           │
  │                          │
  │  [역할 2] 5090 클라이언트│
  │  (평상시 3060과 동일)    │
  └──────────────────────────┘
           │ 데이터/제어
           ▼
  RTX 3060 (클라이언트)
  ┌──────────────────────────┐
  │  TELEOP_DOCKER           │
  │  RViz 2                  │
  │  Recon 에이전트          │
  └──────────────────────────┘
```

### 4070 이중 역할 상세

| 상황 | 4070의 역할 | 이 레포의 활성 여부 |
|------|-------------|--------------------|--|
| **5090 정상** | 5090의 클라이언트 (3060과 동일) | 대기 상태 |
| **5090 장애** | 긴급 대체 서버로 전환, MuJoCo 시뮬 실행 | **활성화** |

### 왜 MuJoCo인가
- Isaac Sim은 RTX 5090급 고사양 필요 → 4070에서 실행 불가
- MuJoCo는 경량 물리 엔진 → RTX 4070에서 전체 시뮬레이션 가능
- 동일한 로봇 모델(dual_openarm.xml)로 연속성 유지

---

## Repository Structure

```
scratch/build_mjcf.py            # SINGLE SOURCE OF TRUTH — 전체 MJCF 모델 생성
urdf/
  dual_openarm.xml               # 컴파일된 MJCF (직접 편집 금지 — build_mjcf.py로 재생성)
  dual_openarm.urdf              # OpenArm URDF (STL 메시 참조 + 댐핑)
  omx_f.urdf                     # 참조용 — 메시는 시스템 ROS 경로에서 로드
  vicpinky.urdf                  # 참조용 — 섀시는 build_mjcf.py에 정의
meshes/                          # OpenArm STL/OBJ 에셋
scripts/
  sim_dual_arm.py               # 메인 시뮬레이션 루프 (MuJoCo + Rerun)
  sim_interactive_ik.py         # 독립형 IK 데모 (ROS 불필요)
  sim_ros2_ik.py                # ROS 2 연동 IK + 인터랙티브 마커
  start_all.sh                  # 최소 실행 (ROS 없음) — 폴백 시나리오 기본
  start_full_sim.sh             # 풀스택 (ROS 2 + RViz + IK 마커)
  check_can.py                  # CAN 버스 하드웨어 점검
  setup_can.sh / setup_can_fd.sh   # CAN / CAN-FD 인터페이스 설정
  teleop_left.sh                # 왼쪽 팔 텔레오퍼레이션 헬퍼
  rviz_interactive_marker.py    # RViz 2 인터랙티브 마커 IK 서버
  run_dashboard.sh              # 대시보드 단독 실행
dashboard/
  main.py                       # FastAPI 상태 대시보드 (포트 8000)
  templates/                    # Jinja2 HTML 템플릿
config/
  dual_arm_config.yaml          # 하드웨어 설정 (CAN 버스, 시리얼, 카메라)
backups/
  2026-05-13_vicpinky_orbit/   # 기준 스냅샷 — XML 드리프트 발생 시 비교
scratch/
  build_mjcf.py                # 모델 빌더 (진실의 단일 출처)
  _ntfy_fmt.py                 # NTFY 알림 포매터
  *.py                         # 일회성 진단/디버그 스크립트
docs/
  10_Daily_Logs/               # Obsidian 세션별 진행 로그
  30_Troubleshooting/          # 이슈 해결 및 예방 가이드
.obsidian/                     # Obsidian 볼트 설정 (수정 금지)
SESSION_*.md                   # 세션 보고서 (레포 루트, Obsidian 노트)
00_Dashboard.md                # Obsidian 프로젝트 대시보드
```

---

## 긴급 폴백 절차 (5090 장애 시)

```bash
# 1. venv 활성화
source /home/moos/dev_ws/dual_arms/venv/bin/activate
export MUJOCO_GL=egl

# 2. 시뮬레이션 + 대시보드 즉시 기동
bash scripts/start_all.sh

# 서비스 확인
# MuJoCo + Rerun → http://localhost:9090
# FastAPI 대시보드 → http://localhost:8000
```

5090 복구 후 → 이 레포 시뮬레이션 중단, 4070을 다시 클라이언트 모드로 전환.

---

## 환경 설정

### Python venv (시스템 Python 3.12)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

venv 경로: `/home/moos/dev_ws/dual_arms/venv` (`start_all.sh` 하드코딩 — 다른 머신이면 수정 필요)

### ROS 2 시스템 패키지 (OMX-F 메시 필요 시)

```bash
sudo apt install ros-jazzy-open-manipulator-description
```

OMX-F STL 메시 경로: `/opt/ros/jazzy/share/open_manipulator_description/meshes/omx_f/`

### 렌더링 환경변수

```bash
export MUJOCO_GL=egl   # Linux 헤드리스 환경에서 안정적 렌더링
```

---

## 실행 방법

### 최소 실행 (ROS 2 없음 — 폴백 시나리오 기본)

```bash
bash scripts/start_all.sh
```

- MuJoCo 뷰어 + Rerun 스트림 → http://localhost:9090
- FastAPI 대시보드 → http://localhost:8000

### 풀스택 (ROS 2 Jazzy + venv에 pyyaml 필요)

```bash
bash scripts/start_full_sim.sh
```

`robot_state_publisher`, RViz 2, 인터랙티브 마커 IK 서버 추가 기동.

> **알려진 문제:** ROS 2 IK 경로 크래시 — `target_left`/`target_right` mocap 바디가 모델에 없음. 사용 전 `scratch/build_mjcf.py`에 추가 필요.

### MJCF 모델 재생성

```bash
python scratch/build_mjcf.py
```

모든 구조 변경(관절 원점, 기하, 댐핑, 조명)은 `build_mjcf.py`에서만 — `urdf/dual_openarm.xml` 직접 편집 금지.

---

## 핵심 컨벤션

### 모델 편집
- `scratch/build_mjcf.py` 수정 → 재생성 → `backups/2026-05-13_vicpinky_orbit/`과 diff 확인
- `lerobot/`은 의도적으로 미추적 — pip으로 업스트림 설치
- 렌더 캡처는 `captures/`에 저장 (gitignore)

### 하드웨어 설정 (`config/dual_arm_config.yaml`)

| 컴포넌트 | 인터페이스 | 설정 |
|---------|-----------|------|
| 왼쪽 팔로워 암 | CAN-FD `can0` | 1 Mbps 명목 / 5 Mbps 데이터 |
| 오른쪽 팔로워 암 | CAN-FD `can1` | 1 Mbps 명목 / 5 Mbps 데이터 |
| 왼쪽 리더 암 | Dynamixel `/dev/ttyUSB0` | 1 Mbps |
| 오른쪽 리더 암 | Dynamixel `/dev/ttyUSB1` | 1 Mbps |
| 상단 카메라 | OpenCV index 0 | — |
| 왼쪽 손목 카메라 | OpenCV index 1 | — |
| 오른쪽 손목 카메라 | OpenCV index 2 | — |

### Obsidian 볼트 컨벤션
- 세션 노트: `SESSION_YYYY-MM-DD_<주제>.md` (레포 루트)
- 내부 링크 `[[경로]]` 형식 — 파일 이동/이름 변경 시 링크 유지 필수
- `.obsidian/` 디렉토리 수정 금지

---

## 의존성 주요 항목

| 패키지 | 버전 | 용도 |
|--------|------|------|
| mujoco | 3.7.0 | 물리 시뮬레이션 |
| rerun-sdk | 0.31.3 | 실시간 3D 시각화 |
| fastapi | 0.136.1 | 상태 대시보드 |
| uvicorn | 0.46.0 | ASGI 서버 |
| python-can | 4.6.1 | CAN 버스 인터페이스 |
| numpy | 2.4.4 | 수치 연산 |
| scipy | 1.17.1 | IK 연산 |
| trimesh | 4.12.0 | 메시 처리 |

---

## ROOPS 멀티 에이전트 컨텍스트

| 콜사인 | 머신 | GPU | 역할 |
|--------|------|-----|------|
| **Aegis** | 원격 서버 | RTX 5090 | Isaac Sim 오케스트레이션, 메인 시뮬 |
| **Moojoco** | 로컬 개발 머신 | RTX 4070 | MuJoCo 폴백 시뮬, 5090 클라이언트 |
| **Recon** | 클라이언트 | RTX 3060 | IK Ready Pose, 텔레오퍼레이션, 모니터링 |
| **Rudex** | Anthropic 클라우드 | — | 코드베이스 관리, 문서화, GitHub 작업 |

> **Rudex** = Rudder(방향타) + dex(기록/색인). 사령관 호출 시 활성화되어 팀의 코드와 기록을 관리한다.

### 통신 인프라
- NTFY 서버: `http://hyperbook.com:8880` (평문 HTTP — TLS 미적용)
- 자격증명: `~/.roops_moojoco_topics.env` — **절대 커밋 금지**
- 토픽명·자격증명은 코드/문서 파일에 포함 금지

### 보안 주의사항 (2026-05-18 기준)
- `moosjiny/mujoco`, `moosjiny/dual_arms` 모두 **Private** 레포
- 클론/풀에 SSH 키 또는 PAT 필요
- 비인증 `api.github.com` 요청은 HTTP 404 반환
- NTFY 평문 HTTP (포트 8880) — TLS 전환 권고

---

## 포트 참조

| 포트 | 서비스 | 활성 시점 |
|------|--------|----------|
| 8000 | FastAPI 대시보드 | 항상 (폴백 시에도) |
| 9090 | Rerun 웹 뷰어 | 항상 (폴백 시에도) |

---

## 미결 이슈

| # | 이슈 | 상태 |
|---|------|------|
| 1 | ROS 2 IK 크래시 — mocap 바디 미생성 | 미해결 |
| 2 | OMX-F 메시가 ROS 시스템 패키지에 의존 | 설계상 의도 |
| 3 | NTFY 서버 평문 HTTP (포트 8880) | TLS 전환 대기 |
| 4 | `roops-agent` R/W 자격증명 노출 (2026-05-18) | 즉시 비밀번호 교체 필요 |
| 5 | L1 GitHub 검증에 인증 토큰 필요 | 관리자가 fine-grained PAT 발급 필요 |
