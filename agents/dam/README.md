# ROOPS-DAM — 분산 연상 메모리

> **"사령관이 손으로 하던 일을 네트워크가 자동으로 한다."**

## 개요

ROOPS-DAM은 ROOPS 팀 에이전트들의 세션 단절 문제를 해결하는 분산 연상 메모리 시스템입니다.
현대 홉필드 네트워크 (Ramsauer et al. 2020)를 기반으로, 에이전트 컨텍스트를 임베딩 벡터로 변환해
팀 공유 네트워크에 저장합니다.

## 왜 만들었나

`ADR_002_HOPFIELD_CACHE_MEMORY_mojo.md` 파일이 Mojo 세션 소멸로 사라졌을 때,
사령관이 과거 Rudex 세션에서 그 내용을 복원했습니다.
이것이 홉필드 원리가 이미 수동으로 작동하고 있었음을 증명했습니다.
ROOPS-DAM은 이 과정을 자동화합니다.

## 설치

```bash
# 최소 설치
pip install numpy requests

# 의미 기반 임베딩 (권장)
pip install sentence-transformers
```

## 빠른 시작

```python
import os
from agents.dam import init_session

# 세션 시작
dam = init_session(
    agent_name="hermes",
    context="오늘 ADR-002 검토 및 thesis 제출 예정",
    api_key=os.environ["DAM_API_KEY"]
)

# 팀 기억 검색
hits = dam.query("홉필드 초안 ADR")
for label, score in hits:
    print(f"{score:.3f}  {label}")

# 세션 종료 전 저장 (atexit으로 자동 호출되지만 명시적으로도 가능)
dam.session_end("오늘 작업 완료", note="ADR-002 복구, thesis v3 제출")
```

## CLI

```bash
export DAM_API_KEY=your_api_key

# 상태 확인
python -m agents.dam.cli --agent hermes status

# 팀 기억 검색
python -m agents.dam.cli --agent hermes query "ADR-002 홉필드"

# 텍스트 저장
python -m agents.dam.cli --agent hermes store "중요한 결정 사항" --note "2026-06-09"

# Phase 1 검증 데모 (복원 정확도 70% 목표)
python -m agents.dam.cli --agent mojo demo
```

## 아키텍처

```
에이전트 컨텍스트 (텍스트)
    │
    ▼ Embedder
임베딩 벡터 (dim=384)
    │
    ▼ ModernHopfield
팀 공유 메모리 뱅크 (n_patterns × 384)
    │
    ▼ WStore
Memory API / 로컬 캐시 (영속 저장)
```

## 에이전트별 API 키 설정

| 에이전트 | 환경변수 |
|---------|----------|
| hermes | `DAM_API_KEY=dg3dyWBrddlUmBGOsdH-...` |
| rudex  | `DAM_API_KEY=PCF4YhGWi1wEcvow2QG0...` |
| mojo   | `DAM_API_KEY=<mojo 키>` |

> **보안:** API 키는 환경변수로만. 코드/로그 하드코딩 금지.

## 구현 로드맵

| Phase | 내용 | 상태 |
|-------|------|------|
| 0 | 임베딩 모델 선택, dim=384 확정 | ✅ 완료 |
| 1 | 단일 에이전트 저장·복원 (70% 목표) | ✅ 구현 완료, 검증 필요 |
| 2 | Rudex ↔ Mojo 크로스 에이전트 | 🔲 미착수 |
| 3 | 6뉴런 전체 팀 네트워크 | 🔲 미착수 |
| 4 | 세션 단절 자동 복원 (50% 단축 목표) | 🔲 미착수 |
| 5 | 멀티모달 (Whisper·CLIP) | 🔲 미착수 |

## 참고

- Ramsauer, H. et al. (2020). *Hopfield Networks is All You Need.*
- ADR-002 설계문서: `dual_arms/docs/ADR_002_HOPFIELD_CACHE_MEMORY_*.md`
- thesis 논문: `roops-dam-design-v1` (thesis.hyperbook.com)
