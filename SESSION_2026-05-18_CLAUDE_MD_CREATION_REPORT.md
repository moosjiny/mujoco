---
tags: project/session-report
status: complete
date: 2026-05-18
author: Claude Code (AI assistant)
---

# CLAUDE.md 생성 작업 보고서

**작업일:** 2026-05-18  
**작업자:** Claude Code (AI 어시스턴트)  
**대상 레포지토리:** `moosjiny/mujoco`, `moosjiny/dual_arms`  
**작업 브랜치:** `claude/add-claude-documentation-jjLM8`  
**상태:** 완료

---

## 1. 작업 개요

두 개의 GitHub 레포지토리(`moosjiny/mujoco`, `moosjiny/dual_arms`)를 분석하여 AI 어시스턴트가 코드베이스를 즉시 파악하고 올바른 컨벤션을 따를 수 있도록 `CLAUDE.md` 파일을 각 레포에 생성하였다.

---

## 2. 레포지토리 분석 결과

### 2-1. `moosjiny/mujoco` — MuJoCo 기반 디지털 트윈

#### 목적
- MuJoCo 3.7.0으로 구현한 **쌍팔 로봇 물리 시뮬레이션**
- 시뮬레이션 대상: OpenArm 팔로워 암 2개 + OMX-F 팔로워 암 + Vic Pinky 모바일 베이스
- Rerun SDK로 실시간 시각화, FastAPI 대시보드로 시스템 상태 모니터링
- ROS 2 Jazzy 선택적 연동 (RViz + 인터랙티브 마커 IK)
- **Obsidian 지식 볼트**로도 활용 — 코드와 세션 노트·문서가 공존

#### 핵심 파일 구조

| 경로 | 역할 |
|------|------|
| `scratch/build_mjcf.py` | **단일 진실 공급원(Single Source of Truth)** — MJCF 모델 생성 |
| `urdf/dual_openarm.xml` | 컴파일된 MJCF (직접 편집 금지) |
| `scripts/sim_dual_arm.py` | 메인 시뮬레이션 루프 |
| `scripts/start_all.sh` | 최소 실행 (ROS 없음) |
| `scripts/start_full_sim.sh` | 전체 스택 (ROS 2 포함) |
| `dashboard/main.py` | FastAPI 상태 대시보드 (포트 8000) |
| `config/dual_arm_config.yaml` | 하드웨어 설정 (CAN 버스, 시리얼, 카메라) |
| `backups/2026-05-13_vicpinky_orbit/` | 기준 스냅샷 |

#### 기술 스택

| 패키지 | 버전 | 용도 |
|--------|------|------|
| mujoco | 3.7.0 | 물리 엔진 |
| rerun-sdk | 0.31.3 | 실시간 3D 시각화 |
| fastapi | 0.136.1 | 상태 대시보드 |
| uvicorn | 0.46.0 | ASGI 서버 |
| python-can | 4.6.1 | CAN 버스 인터페이스 |
| scipy | 1.17.1 | IK 연산 |

#### 주요 컨벤션
- MJCF 모델 변경 시 반드시 `scratch/build_mjcf.py`를 수정 후 재생성
- 재생성 후 `backups/2026-05-13_vicpinky_orbit/`과 diff하여 의도치 않은 변경 확인
- 세션 노트는 `SESSION_YYYY-MM-DD_<주제>.md` 형식으로 루트에 저장
- Obsidian 내부 링크(`[[경로]]`) 유지 필수

#### 미결 이슈
- ROS 2 IK (`sim_ros2_ik.py`) 크래시 — `target_left`/`target_right` 목표 바디 미생성
- OMX-F 메시 파일이 ROS 시스템 패키지에 의존 (번들 불포함)
- NTFY 서버 평문 HTTP 운영 중 (TLS 미적용)

---

### 2-2. `moosjiny/dual_arms` — Isaac Sim 기반 시뮬레이션

#### 목적
- **Isaac Sim 4.2.0 + Isaac Lab** 기반의 고성능 GPU 서버 시뮬레이션
- 원격 서버(RTX 5090)에서 실행, WebRTC로 클라이언트(RTX 3060)에 스트리밍
- ROOPS 멀티 에이전트 통신 인프라 포함
- USD 에셋 변환 파이프라인, cuRobo 모션 플래닝 포함

#### 시스템 구조

```
[서버: RTX 5090]
dual_arms_v5_stable  →  Isaac Sim headless + ROS 2 하트비트
dual_arms_viewer     →  Isaac Sim WebRTC 시각화 (포트 8211)
FastDDS Discovery    →  포트 8219

[클라이언트: RTX 3060]
TELEOP_DOCKER        →  RViz 2, WebSocket 클라이언트, Recon 스크립트

SSH 터널: 8214(VNC), 8516(JSON JointState 양방향)
```

#### 2개 컨테이너 구조 이유
Isaac Sim의 Kit 프레임워크는 **프로세스당 SimulationApp 1개만 허용**한다. 헤드리스 시뮬레이션과 WebRTC 시각화가 서로 다른 Kit 파일을 필요로 하므로, 현재는 두 컨테이너로 분리 운영한다. Phase 2에서 단일 스크립트로 통합 예정.

#### 주요 스크립트 분류

| 분류 | 대표 스크립트 |
|------|---------------|
| Isaac Sim 시뮬 | `recon_fixed_sim_lab.py`, `view_robot_webrtc.py` |
| 에셋 변환 | `convert_omx_to_usd_v4.py`, `inject_physics.py`, `relink_meshes.py` |
| 검사 도구 | `inspect_usd.py`, `inspect_physics.py`, `inspect_full.py` |
| 스폰 테스트 | `test_all_robots_spawn_final.py`, `test_bimanual_only.py` |
| AI 통신 | `ai_comm_bridge.py`, `sync_ai_logs.py` |
| 텔레옵 | `teleop_bridge.py`, `dual_arm_servo_node.py` |
| 모니터링 | `server_log_monitor.py`, `recon_monitor.py` |

#### Phase 진행 상황

| Phase | 목표 | 상태 |
|-------|------|------|
| 1 | 개별 로봇·기능 검증 | 진행 중 |
| 2 | 단일 컨테이너 통합 (WebRTC+시뮬) | 계획됨 |
| 3 | IK 제어, 멀티 환경, 대시보드 연동 | 미래 |

#### 검증 완료 로봇

| 로봇 | DOF | 상태 |
|------|-----|------|
| Wowrobo Bimanual OpenArm | 18 | 스폰 완료, T포즈 확인 |
| OMX-F 팔로워 암 | 6 | 스폰 완료, 메시 확인 |
| Vic Pinky 모바일 베이스 | — | 스폰 완료, 메시 확인 |

#### 미결 이슈
- `requirements.txt` 머지 충돌 미해결 (`pip install` 전 수동 해결 필요)
- NTFY 서버 평문 HTTP (TLS 미적용)
- `roops-agent` R/W 자격증명 평문 노출 (2026-05-18) — 즉시 비밀번호 회전 필요
- L1 GitHub 검증에 인증 토큰 필요 (두 레포 모두 Private 전환됨)

---

## 3. ROOPS 멀티 에이전트 시스템 요약

ROOPS(Robot-Oriented Operation/Programming System)는 Isaac Sim·MuJoCo 등 시뮬레이터에 무관하게 동일한 인터페이스로 로봇을 제어하기 위한 추상화 레이어다.

### 에이전트 역할표

| 콜사인 | 위치 | 담당 레포 | 역할 |
|--------|------|-----------|------|
| **Aegis** | 서버 (RTX 5090) | `dual_arms` | Isaac Sim 오케스트레이션, 인프라 관리 |
| **Recon** | 클라이언트 (RTX 3060) | `dual_arms` (client/) | IK Ready Pose, 시각화, 모니터링 |
| **Moojoco** | 개발 머신 | `mujoco` | MuJoCo 디지털 트윈, 모델 무결성 |

### 통신 채널

| 채널 | 프로토콜 | 주소 | 용도 |
|------|----------|------|------|
| ROS 2 토픽 | FastDDS | Discovery 포트 8219 | `/ai/heartbeat/server`, `/ai/comm_log` |
| NTFY | HTTP | `hyperbook.com:8880` | 에이전트 알림, 브로드캐스트 |
| WebSocket | TCP | 포트 8516 | 실시간 JointState 스트리밍 |
| SSH 터널 | TCP | 8214 / 8516 | VNC 스트림 / JSON 데이터 |

---

## 4. 보안 현황 (2026-05-18 기준)

| 항목 | 상태 | 권고 |
|------|------|------|
| 두 레포 Private 전환 | 완료 (2026-05-18) | 클론 시 SSH 키 또는 PAT 필요 |
| `roops-agent` R/W 자격증명 노출 | 발생 (roops-comm 채널) | 비밀번호 즉시 회전 |
| NTFY 서버 TLS 미적용 | 평문 HTTP (8880) | `https://hyperbook.com` TLS 적용 권고 |
| Slack→ntfy 브리지 세션 출력 유출 | 발생 (필터 없음) | 브리지 필터링 설정 필요 |
| Moojoco L1 검증용 PAT | 미발급 | 관리자가 fine-grained PAT 발급 필요 |

---

## 5. 생성된 파일

| 레포 | 파일 | 브랜치 | 커밋 SHA |
|------|------|--------|---------|
| `moosjiny/mujoco` | `CLAUDE.md` | `claude/add-claude-documentation-jjLM8` | `c7eb2b2` |
| `moosjiny/dual_arms` | `CLAUDE.md` | `claude/add-claude-documentation-jjLM8` | `809a609` |
| `moosjiny/mujoco` | `SESSION_2026-05-18_CLAUDE_MD_CREATION_REPORT.md` | `claude/add-claude-documentation-jjLM8` | (본 파일) |

---

## 6. CLAUDE.md 주요 포함 내용

각 `CLAUDE.md`는 다음 항목을 포함한다:

1. **레포 개요** — 목적, AI 에이전트 콜사인
2. **디렉터리 구조** — 각 파일/폴더의 역할
3. **환경 설정** — venv, ROS 패키지, Docker, 환경 변수
4. **실행 방법** — 단계별 시작 명령어
5. **핵심 컨벤션** — 모델 편집 원칙, 파일명 규칙, 볼트 관리
6. **의존성 목록** — 주요 패키지 버전
7. **ROOPS 컨텍스트** — 에이전트 역할, 통신 인프라, 보안 주의사항
8. **포트 참조표** — 서비스별 포트 번호
9. **미결 이슈** — 현재 알려진 버그·제약사항

---

*기록: Claude Code — 2026-05-18*
