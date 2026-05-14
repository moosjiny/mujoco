---
date: 2026-05-07
tags: session/log, mujoco, digital-twin
type: progress
---

# 📅 2026-05-07 세션 진행 정리

> [!success] 오늘 완료한 주요 성과
> - MuJoCo 물리 엔진(충돌 감지) 활성화 완료
> - EGL 백엔드 적용으로 렌더링 품질 개선
> - Dual Arm + OMX-F + ViC-Pinky 3종 로봇 통합 모델 구축

---

## 🛠️ 작업 세부 내용

### 1. 물리 엔진 활성화 (MuJoCo Physics)
- **이전 상태**: `mj_kinematics` 만 사용 → 관절이 물리 법칙 없이 텔레포트처럼 움직임 (충돌 없음)
- **변경 내용**:
  - `scratch/build_mjcf.py` 수정: 모든 geom에 `contype=1, conaffinity=1` 적용
  - 액추에이터를 **Position Control** (gaintype=FIXED, biastype=AFFINE, kp=200)으로 변경
  - `scripts/sim_dual_arm.py` 수정: `mj_kinematics` → **`mj_step` (10 substeps/frame)**
- **결과**: 물리 충돌 감지가 활성화되어 관절이 겹치지 않음

### 2. 렌더링 개선 (EGL 백엔드)
- **문제**: MuJoCo 내장 뷰어에서 화면 렌더링 깨짐 현상 발생
- **해결**: `scripts/start_all.sh`에 `export MUJOCO_GL=egl` 추가
- **결과**: 깨끗한 3D 렌더링으로 MuJoCo 내장 뷰어 정상 동작

### 3. 디지털 트윈 시스템 구축
- **MuJoCo 내장 뷰어** + **Rerun 웹 뷰어** + **FastAPI 대시보드** 세 가지 동시 연동
- `scripts/sim_dual_arm.py`:
  - `mujoco.viewer.launch_passive()` 로 내장 뷰어 활성화
  - `rr.serve_grpc(grpc_port=9876)` + `rr.serve_web_viewer(web_port=9090)` 로 Rerun 연동
  - 초당 10회 `POST /update` 로 대시보드에 관절 위치 + 토크 실시간 전송
- `dashboard/main.py`: `POST /update` 엔드포인트 추가, WebSocket으로 실시간 데이터 브라우저에 전달

### 4. OMX-F + ViC-Pinky 모델 통합
- **URDF 정리**:
  - [[urdf/omx_f.urdf]]: `omx_f_clean.urdf` 복사 (5-DOF 팔로워 암, meshes 없음 → BOX로 대체)
  - [[urdf/vicpinky.urdf]]: 중복 `<inertial>` 태그 문제 수정 후 완전히 재작성 (단순화)
- **통합 결과**: `scratch/build_mjcf.py` 수정 → `urdf/dual_openarm.xml` 재빌드
  - **최종 모델**: `njnt=27`, `nu=25`

---

## 📁 핵심 파일 목록

| 파일 | 역할 | 상태 |
|---|---|---|
| [[scripts/sim_dual_arm.py]] | 메인 시뮬레이션 | ✅ 업데이트 완료 |
| [[scripts/start_all.sh]] | 전체 시스템 시작 스크립트 | ✅ 업데이트 완료 |
| [[scratch/build_mjcf.py]] | URDF → MJCF 변환 | ✅ 업데이트 완료 |
| [[urdf/dual_openarm.xml]] | 최종 MuJoCo 모델 | ✅ 빌드 완료 |

---

## ⚠️ 해결해야 할 이슈

> [!warning] 1. OMX-F 메쉬 파일 누락
> `omx_f.urdf`에 STL 메쉬 파일 경로가 있으나 현재 환경에 파일이 없어 박스 형태로 대체됨. ROBOTIS 공식 저장소에서 meshes를 가져와야 함.

> [!info] 2. ViC-Pinky 단순화 문제
> 현재 본체와 바퀴만 남은 상태. 칼럼, 선반, LiDAR 등을 복원하는 작업 필요.

---

## 🚀 내일 시작 방법

```bash
cd /home/moos/dev_ws/dual_arms
bash scripts/start_all.sh
```

---

## 💻 환경 정보
- **GPU**: RTX 4070 (Driver 595.58.03, CUDA 13.2)
- **MuJoCo**: 3.7.0 (Rendering: GPU/EGL)
- **Python**: 3.12 (venv)
