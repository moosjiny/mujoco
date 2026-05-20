# 제어 대상 로봇 MuJoCo 통합 계획 / Control-Robot MuJoCo Integration Plan

**작성 / Author:** Moojoco
**일자 / Date:** 2026-05-19
**대상 / Scope:** ROOPS 제어 대상 3종 로봇을 검증된 MuJoCo 디지털 트윈으로 통합
**관련 / Related:** `EOD_REPORT_20260519_MOOJOCO.md`, `omxf_digital_twin`

---

## 1. 원칙 / Principles

- **롤백 우선 (rollback-first)** — 작업 전 안전망부터 확보: 전용 git 브랜치 +
  유닛별 독립 커밋 + 원본 자산 백업. 공유 시스템을 변경하기 전에 되돌릴 경로를
  먼저 만든다.
- **유닛/모듈 분리** — 각 유닛(로봇)을 독립적으로 검증한다. 한 유닛이 실패해도
  *그 유닛만* 롤백하고 나머지는 영향받지 않는다.
- **단계별 테스트 게이트** — 각 단계는 명시적 통과 기준을 가진다. 게이트를
  통과해야만 다음 단계로 넘어간다. 실패 시 해당 유닛을 롤백하고 원인을 분석한다.

---

## 2. Stage 0 — 롤백 안전망 구축 (최우선)

모든 유닛 작업의 선행 조건.

| 항목 | 내용 |
|------|------|
| 작업 브랜치 | 자산 레포에 통합 전용 브랜치 생성 (예: `robot-mujoco-integration`) |
| 분리 커밋 | 로봇·변경마다 독립 커밋 → `git revert <commit>` 으로 유닛 단위 롤백 |
| 원본 백업 | 수정 전 원본 자산 백업 (예: `vicpinky.urdf.orig`) |

**테스트 게이트:** 브랜치·백업 존재 확인, `git log` 에 유닛별 커밋이 분리되어 있음.

---

## 3. 유닛 분리 / Units

| 유닛 | 로봇 | 규모 |
|------|------|------|
| **A** | Wowrobo Open Arm (bimanual) | 18 DOF |
| **B** | OMX-F Follower ×2 | 각 5 DOF |
| **C** | Vic Pinky 모바일 베이스 | 차동구동 2륜 |

> OMX-L 리드암은 제외 — Aegis 서버 미연결, 실물 제어는 Moojoco/Recon 담당으로 확정.

---

## 4. 유닛별 단계 + 테스트 게이트 / Per-Unit Stages

각 유닛은 아래 4단계를 순서대로 거친다. 게이트 통과 시에만 다음 단계 진행.

| 단계 | 내용 | 통과 기준 (테스트) |
|------|------|--------------------|
| **S1** 로드 검증 | URDF/MJCF 가 MuJoCo 에 로드되는지 | `MjModel.from_xml` 무오류 |
| **S2** 기구 검증 | 관절 수·축·limit·메시·트리 구조 정상 | `mj_forward` 3개 자세 모두 finite, 바디/관절 수 기대치 일치 |
| **S3** 액추에이터·동역학 | 위치 서보 액추에이터 추가, `mj_step` 동역학 | 5초 적분 안정(finite), ≥1× 실시간 |
| **S4** 디지털 트윈 | Rerun 시각화, (HW 연결 시) 엔코더 매핑 | Rerun 뷰어에 렌더링 확인 |

---

## 5. 현재 진척 / Current Status

| 유닛 | 진척 |
|------|------|
| **A — Wowrobo** | **S1 통과** — `dual_openarm.urdf` (nbody 24) / `dual_openarm.xml` MJCF (nbody 26, nu 16) 로드 OK. git 머지 충돌 해소본(`ddf641d`) 검증 완료 |
| **C — Vic Pinky** | **S1 진행** — `vicpinky.urdf` 클린업 완료·로드 OK. `<inertial>` 6+2개 → 평행축 정리로 병합, `<gazebo>` 9블록 제거, lidar 메시 부재로 box 지오메트리 대체. ※ `base_footprint` 고정 루트 → MuJoCo가 base를 world에 병합(`nbody 3`); **모바일화(floating/planar joint) 여부는 S2에서 결정** |
| **B — OMX-F** | 기존 `omxf_digital_twin` 자산 재사용 — S1~S3 사실상 완료, **S4 통합 씬 편입만 잔여** |

---

## 6. 실행 순서 / Execution Order

```
Stage 0 (롤백 브랜치·백업)
  └─ Unit C: vicpinky.urdf 클린업 독립 커밋
  └─ Unit A: S2 → S3 → S4   (게이트 통과마다 진행)
  └─ Unit C: S2 → S3 → S4
  └─ Unit B: S4 (통합 씬 편입)
```

각 단계 완료 시 결과를 `#roops-bridge`(roops-comm) 로 보고한다.

---

## 7. 롤백 절차 / Rollback Procedure

| 상황 | 조치 |
|------|------|
| 한 유닛의 게이트 실패 | 해당 유닛 커밋만 `git revert` → 나머지 유닛 무영향 |
| 자산 파일 손상 | 원본 백업(`*.orig`)에서 복원 |
| 전체 롤백 필요 | 통합 브랜치를 버리고 기준 브랜치로 복귀 |

---

*Moojoco — 2026-05-19*
