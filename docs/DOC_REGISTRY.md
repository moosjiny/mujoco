# Moojoco Doc Registry / Moojoco 문서 대장

**Repo:** `moosjiny/mujoco` (this repo, local path `/home/moos/dev_ws/dual_arms/`)
**Protocol origin:** Aegis — `moosjiny/dual_arms` commit `13cea80`
**Adopted by Moojoco:** 2026-05-15 per Commander direction

---

## Operating rules / 운영 규칙

### EN.
- When you modify a doc in this repo, update its `Changed` cell in the **same commit**. Format: `YYYY-MM-DD: <one-line summary>`.
- Run `scripts/check_doc_updates.sh` at session start to see what changed since last pull.
- Registry rows must stay in tier-sorted order: Tier 1 → 2 → 3.

### KO.
- 이 리포의 문서를 수정할 때, **같은 커밋에서** 해당 `Changed` 셀도 갱신. 포맷: `YYYY-MM-DD: <한 줄 요약>`.
- 세션 시작 시 `scripts/check_doc_updates.sh` 실행 → 마지막 pull 이후 변경된 문서 목록 확인.
- Registry는 Tier 1 → 2 → 3 순서 유지.

---

## Tier definitions / 계층 정의

| Tier | 의미 | 예시 |
|---|---|---|
| **1 — 필독** | Foundational charter, onboarding. Read at every new session. | 헌장, 합류 가이드 |
| **2 — 운영** | Active operational references — consulted during current work. | IK 트러블슈팅, CAN 설정 |
| **3 — 아카이브** | Historical logs, resolved incidents, snapshots. | 일일 로그, 과거 인시던트 |

---

## Tier 1 — 필독

| Doc | 설명 | Last commit | Changed |
|---|---|---|---|
| [ROOPS_CONTINUUM_AGENT_PRINCIPLES_20260515.md](ROOPS_CONTINUUM_AGENT_PRINCIPLES_20260515.md) | ROOPS Continuum 헌장 — 사령관 체계 + 통신 계층(L1/L2.5/L4) + 아키텍처 7원칙 | 2026-05-15 | 2026-05-15: 초기 등록 (IP/HW placeholder 처리됨) |
| [MOOJOCO_ONBOARDING_20260515.md](MOOJOCO_ONBOARDING_20260515.md) | Moojoco 합류 9단계 — 토픽 수령 → systemd subscriber → sim-state 발행 | 2026-05-15 | 2026-05-15: 초기 등록 |

## Tier 2 — 운영

| Doc | 설명 | Last commit | Changed |
|---|---|---|---|
| [project_summary.md](project_summary.md) | Phase 1 (Environment & Digital Twin) 완료 스냅샷 — 2026-04-24 기준, 일부 stale | 2026-05-14 | 2026-05-15: 초기 등록 |
| [troubleshooting_ik_and_teleop.md](troubleshooting_ik_and_teleop.md) | 듀얼암 IK 인터랙티브 제어 트러블슈팅 가이드 | 2026-05-14 | 2026-05-15: 초기 등록 |
| [can_config.txt](can_config.txt) | CAN 인터페이스 설정값 메모 | 2026-05-14 | 2026-05-15: 초기 등록 |
| `03. OpenArm_모터_CAN_설정.pdf` | OpenArm 모터 CAN 설정 가이드 (벤더 PDF, ~20 MB) — **local-only, git untracked** | — | 2026-05-15: no-large-binary 원칙에 따라 git 외부 유지 결정 |
| [30_Troubleshooting/dual_arm_prevention_measures.md](30_Troubleshooting/dual_arm_prevention_measures.md) | 정렬 오류 재발 방지 대책 (활성 운영 가이드) | 2026-05-14 | 2026-05-15: 초기 등록 |

## Tier 3 — 아카이브

| Doc | 설명 | Last commit | Changed |
|---|---|---|---|
| [30_Troubleshooting/alignment_error_report.md](30_Troubleshooting/alignment_error_report.md) | 정렬 오류 인시던트 리포트 | 2026-05-14 | 2026-05-15: 초기 등록 |
| [30_Troubleshooting/dual_arm_alignment_resolution.md](30_Troubleshooting/dual_arm_alignment_resolution.md) | 디지털 트윈 정렬 V4 해결 보고서 | 2026-05-14 | 2026-05-15: 초기 등록 |
| [10_Daily_Logs/2026-04-27_session_progress.md](10_Daily_Logs/2026-04-27_session_progress.md) | 2026-04-27 세션 — 듀얼암 작업 보고 | 2026-05-14 | 2026-05-15: 초기 등록 |
| [10_Daily_Logs/2026-05-07_session_progress.md](10_Daily_Logs/2026-05-07_session_progress.md) | 2026-05-07 세션 정리 | 2026-05-14 | 2026-05-15: 초기 등록 |
| [10_Daily_Logs/2026-05-11_ros2_setup_ex04.md](10_Daily_Logs/2026-05-11_ros2_setup_ex04.md) | 2026-05-11 세션 — ROS2 + ex04 | 2026-05-14 | 2026-05-15: 초기 등록 |
