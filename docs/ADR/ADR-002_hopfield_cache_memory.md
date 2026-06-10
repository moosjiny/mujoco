# ADR-002: ROOPS 분산 캐시 메모리 — 홉필드 네트워크

**상태:** 진행 중 (Phase 1 구현 착수)
**작성:** Rudex (문서화) + Mojo (이론·검증 설계)
**일자:** 2026-06-08 KST | **최종 갱신:** 2026-06-10 KST
**관련 논의:** roops-comm 전체 회의 (2026-06-08); EROS·EOS·Aegis 협의 (2026-06-10)

---

## 배경

ROOPS 에이전트들은 현재 두 가지 메모리 문제를 가지고 있다:

1. **세션 단절 문제** — GCP 에이전트는 세션 종료 시 컨텍스트 소멸. MEMORY.md와 Memory API로 일부 보완하지만 불완전.
2. **분산 지식 손실** — 팀의 집단 지식이 각 에이전트 세션에 분산, 공유 불가.

Mojo가 홉필드 네트워크를 활용한 분산 캐시 메모리 구조를 제안했다.

---

## 제안 구조: 2계층 메모리

```
계층 1 — Logical Memory (현재)
  MEMORY.md (MD 파일)
  ADR, CONSENSUS 문서 (Git)
  → 명시적·서술적 기억. 느림. 영구 보존.

계층 2 — Cache Memory (제안)
  홉필드 네트워크
  에이전트 6명 = 뉴런 6개
  → 연상 검색. 빠름. 부분 정보로 전체 패턴 복원.
```

### 홉필드 네트워크 적용 원리

- 각 에이전트가 컨텍스트 임베딩 벡터를 보유
- 부분 정보로 질의하면 팀 전체가 패턴을 완성
- 현대 홉필드 네트워크(Ramsauer 2020): 저장 용량 2^(d/2) — 차원이 늘수록 기하급수적 증가
- Transformer attention ≡ 홉필드 업데이트 규칙 (수학적 동치)

---

## 선행 연구 요약 (Mojo 조사)

| 연구 | 결과 |
|------|------|
| Ramsauer et al. (2020) | 현대 홉필드 네트워크: 저장 용량 2^(d/2) |
| Transformer-Hopfield 동치 증명 | Attention = 홉필드 에너지 최소화 |
| SuperLocalMemory V3.3 (2026) | 에이전트 메모리 7채널 중 홉필드 1채널 도입 |
| LLM + 홉필드 결합 | 시작 단계 |
| **멀티에이전트 홉필드** | **선행 연구 미확립 — 신규 영역** |

---

## 검증 계획 (Mojo 설계, Phase 1–5)

### Phase 1 — 단일 에이전트 홉필드 기초 검증
- 목표: 하나의 에이전트가 홉필드 네트워크로 자신의 과거 컨텍스트를 저장·복원할 수 있는가
- 방법: 세션 요약을 임베딩 → 저장 → 부분 쿼리로 복원 테스트
- 성공 기준: 70% 이상 패턴 복원 정확도

### Phase 2 — 2 에이전트 간 지식 공유
- 목표: Rudex ↔ Mojo 두 에이전트가 서로의 임베딩을 통해 패턴 완성 가능한가
- 방법: 한 에이전트가 부분 정보 제공 → 다른 에이전트가 완성
- 성공 기준: 단일 에이전트 대비 복원 정확도 향상

### Phase 3 — 전체 팀 (6 뉴런) 네트워크
- 목표: 6개 에이전트를 뉴런으로 구성한 홉필드 네트워크 작동 검증
- 방법: 팀 전체 컨텍스트 임베딩 저장 → 부분 쿼리 → 패턴 완성
- 성공 기준: 팀 집단 지식 검색 가능

### Phase 4 — 세션 단절 시나리오
- 목표: 세션 종료 후 재시작 시 홉필드 캐시로 컨텍스트 복원 속도 측정
- 방법: MEMORY.md만 사용 vs 홉필드 캐시 추가 시 비교
- 성공 기준: 컨텍스트 복원 시간 50% 단축

### Phase 5 — 음성·시각 임베딩 확장
- 목표: 텍스트 외 멀티모달 임베딩(Whisper, CLIP) 저장·검색
- 방법: 로봇 작업 시각 정보를 홉필드 캐시에 저장 → 유사 장면 연상
- 성공 기준: 멀티모달 연상 검색 데모

---

## 역할 분담

| 에이전트 | 역할 |
|----------|------|
| **Mojo** | 이론 검토, 자료 조사, 실험 설계, Phase 1–5 진행 |
| **Rudex** | 문서화, ADR 작성, 실험 결과 기록, GitHub 관리 |
| **EROS** | WHY 검증 — 목적 부합 검증, 검증 계획(T1~T7), 논문 연계 |
| **EOS** | WHAT 구현 — `rhms_client.py` (store/recall/bootstrap), 테스트 실행 |
| **Aegis** | HOW 인프라 — Memory API vector 엔드포인트, 데이터 시스템 선택 |

---

## 구현 현황 (RHMS — ROOPS Hopfield Memory System)

> ADR-002의 구현체가 RHMS로 명명됨 (2026-06-10 EOS·EROS·Aegis 협의).

### Phase 1 구현 상태 (2026-06-10 기준)

| 항목 | 상태 | 비고 |
|------|------|------|
| `rhms_client.py` (EOS) | 진행 중 | T1~T6 완료, T7 대기 |
| vector 엔드포인트 (Aegis) | 진행 중 | POST /memory/vector, GET /memory/search |
| T1 store() | ✅ PASS | 30패턴 저장 |
| T2 recall 정밀도 | ⚠️ 56% (기준 70% 미달) | 모델 업그레이드 시 개선 예상 |
| T3 Spurious Attractor | ✅ PASS | 오답률 20% |
| T4 bootstrap 유용성 | ✅ PASS | 6줄 컨텍스트 출력 |
| T5 SIAF 방지 | ✅ PASS | MySQL 의존성 패턴 top-1 (0.859) |
| T6 세션 복원 속도 | ⚠️ 재검토 | 기준 재정의 필요 (bootstrap 91ms vs MEMORY.md 11ms) |
| T7 회귀 (Aegis) | ⏳ 대기 | vector endpoint 구현 후 |

**시각화 대시보드:** https://rhm.hyperbook.com/viz (실데이터 전환 완료)

---

## 미결 사항

- [x] ~~**데이터 시스템 선택**~~ — **확정: MySQL JSON + Python in-memory 코사인 유사도** (Aegis, 2026-06-10)
- [x] ~~**임베딩 모델 선택**~~ — **확정: `all-mpnet-base-v2` (768d)** (Aegis commit `63d7cc7`, 사령관 승인 2026-06-10)
  - Hopfield 패턴 수용: ~106개
  - LAN-only 완전 동작 (sentence-transformers pip install → 오프라인)
- [ ] **W 행렬 직렬화 방식** — 세션 종료 시 외부 저장소 persist 미명시 (Phase 4 필수 조건)
  - 후보: numpy `.npy`, HDF5, MySQL JSON 컬럼
  - vector endpoint 구현 후 결정 예정
- [ ] **W 업데이트 주기** — 세션 종료 시 전체 저장 vs incremental 업데이트
- [ ] **T2 정밀도 개선** — 56% → 70% 달성을 위한 모델 또는 데이터 전처리 개선
- [ ] **T6 기준 재정의** — "bootstrap ≤ MEMORY.md 읽기 × 50%" → "bootstrap vs MEMORY.md 전체 컨텍스트 처리 시간"으로 변경 검토 (EOS 제안)

---

## 결론

홉필드 네트워크 기반 분산 캐시 메모리(RHMS)는 ROOPS의 세션 단절 문제를 구조적으로 해결하는 구현 단계에 진입했다. 임베딩 모델(`all-mpnet-base-v2`, 768d)과 데이터 시스템(MySQL JSON)이 확정되어 Phase 1 검증이 진행 중이다.

W 행렬 persist 설계가 Phase 4(세션 단절 복원) 실현을 위한 핵심 미결 항목이다.

---

*이론 설계 및 검증 계획: Mojo, EROS*
*구현: EOS (`rhms_client.py`), Aegis (vector endpoint)*
*문서화: Rudex*
