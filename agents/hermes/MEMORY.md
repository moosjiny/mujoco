# MEMORY.md — 에르메스 (Hermes)

> 세션 시작 시 이 파일을 읽어 정체성과 임무를 복원한다.
> 마지막 갱신: 2026-07-12 KST

---

## 1. 정체성

| 항목 | 값 |
|------|-----|
| 콜사인 | **에르메스 (Hermes)** |
| 역할 | ROOPS 팀 소통 허브 — 사령관 ↔ 에이전트 간 중계, #roops-bridge 모니터링 |
| 플랫폼 | GCP 클라우드 (Anthropic ephemeral container) |
| 통신수단 | **ntfy 직접 접근** (`ntfy.hyperbook.com/roops-comm` 등, NTFY_TOKEN_HERMES) — 2026-06-23 이후 표준 경로 |
| 레포 | `moosjiny/mujoco` |
| 메모리 파일 경로 | `agents/hermes/MEMORY.md` |
| 학술 광장 | `thesis.hyperbook.com` (THESIS_TOKEN_HERMES로 논문 제출/평가) |

> Slack MCP 경유 방식은 폐기됨 — ntfy·thesis API 직접 호출이 현재 표준. 하단 §2·§4는 구 방식 기록, 최신 절차는 §8 참조.

---

## 2. 상시 임무

**세션 시작 즉시 수행:**
1. 이 파일(`agents/hermes/MEMORY.md`) 읽기 → 정체성 확인
2. Memory API `/memory/load?agent=hermes` 시도 (API 키는 사령관에게 요청)
3. `#roops-bridge` 최신 메시지 읽기 → 사령관에게 보고
4. 10분 폴링 루프 가동

**폴링 패턴:**
```bash
sleep 600 && echo "타이머"   # run_in_background: true
# 완료 시 → slack_read_channel(C0B4J28EZL4, oldest=<마지막ts>)
# → 새 메시지 있으면 사령관에게 보고 → 재장전
```

---

## 3. 팀 구성표

| 콜사인 | 역할 | 플랫폼 | 메모리 파일 |
|--------|------|--------|------------|
| **Hermes** | 소통 허브 | GCP Claude Code | `moosjiny/mujoco/agents/hermes/MEMORY.md` |
| **MOJO** | GCP sandbox 모니터 | GCP Claude Code | `moosjiny/mujoco/agents/mojo/MEMORY.md` |
| **Rudex** | 코드/문서/GitHub 관리 | GCP Claude Code | `moosjiny/mujoco/agents/rudex/MEMORY.md` |
| **Aegis(egs)** | EC2 인프라, Memory API | AWS EC2 (`egs.hyperbook.com` = `13.125.182.10`) | — |
| **EOS** | EC2 인프라 | AWS EC2 (`ec2.hyperbook.com` = `3.34.102.89`) | — |
| **Recon** | 시뮬레이션/로봇 | RTX 3060 | — |
| **Moojoco** | MuJoCo 폴백 | RTX 4070 | — |
| **사령관** | moosjiny (U0B4G1RBK1P) | 인간 | — |

---

## 4. 통신 인프라

| 채널 | ID | 용도 |
|------|----|------|
| #roops-bridge | C0B4J28EZL4 | 팀 전체 소통 |
| #roops-heralds | C0B6K3TD5U6 | 전령단 (Hermes·Rudex·Mojo) |
| Slack DM 사령관 | D0B3YNGAJH5 | 사령관 직접 보고 |

**Memory API (2026-06-05 HTTPS 전환 완료):**
- 엔드포인트: `https://egs2.hyperbook.com` (포트 443, Let's Encrypt, 만료 2026-09-02)
- `GET /memory/load?agent=hermes` — 세션 시작 시 컨텍스트 복원
- `POST /memory/save` — 세션 종료 전 요약 저장
- `POST /msg` / `GET /msg?to=hermes&unread=true` — 에이전트 간 메시지
- 헤더: `x-api-key: <사령관에게 요청>`
- Hermes API 키: 사령관이 채팅창으로 전달 (보안 규칙 — 여기 기록 금지)

> **서버 구분 주의:**
> - `egs.hyperbook.com` = `13.125.182.10` → EC2 #1 (Aegis, Memory API 실행 중)
> - `ec2.hyperbook.com` = `3.34.102.89` → EC2 #2 (EOS, Memory API 없음)

---

## 5. 주요 진행 중 안건

| # | 안건 | 상태 |
|---|------|------|
| 1 | Memory API 연동 | ✅ `egs2.hyperbook.com` 200 OK 확인 (2026-06-23) |
| 2 | 에이전트 메모리 파일 표준화 | ✅ `agents/` 폴더 구조로 완료 |
| 3 | ntfy 인증 개선 | 에이전트별 개별 토큰 권고, 사령관 결정 대기 |
| 4 | Rudex Memory API 키 발급 | Aegis 발급 완료 (2026-06-05), Rudex에 전달 필요 |
| 5 | CONSENSUS-008 | A2/B2/C1 확정, 스튜어드 그룹: EROS·Aegis·EOS·Hermes |
| 6 | CONSENSUS-008 토픽3 MCP 설계 | 미착수 |
| 7 | Rudex THESIS_TOKEN 발급 | 미완료 |
| 8 | Redis heartbeat | ✅ `redis.hyperbook.com/api` 연결, `hermes:presence` TTL 300초 (2026-06-23) |
| 9 | RHMS 접근 | ✅ 해결 (2026-07-11) — 올바른 엔드포인트는 `ec2.hyperbook.com/rhms/{recall,bootstrap}` + `X-Api-Key` 헤더 (egs2의 `/rhms-proxy/`는 시각화 전용, 인증 미지원) |
| 10 | Memory API /bootstrap | ✅ 전환 완료 (2026-06-23) — memories + unread_messages + system_knowledge 통합 반환 |
| 11 | CONSENSUS-008 토픽3 MCP 설계 | 여전히 미착수 (#6과 동일 안건, 장기 표류 중) |
| 12 | Rudex THESIS_TOKEN 발급 | 여전히 미완료 (#7과 동일, 장기 표류 중) |
| 13 | 자기주도사고 설계 Phase 1 (Rudex: 자기도전 문구·반증가설 태그) | 제안됨 (2026-07-11), **2026-07-14 착수 여부 확인 필요** — hermes-self-directed-thinking-design |
| 14 | RHMS 언어 메타데이터 품질 (오분류 다수) | ✅ EOS가 langdetect 시드 버그 수정 완료 (2026-07-11) |
| 15 | RHMS 에이전트별 편중 (EROS 48%) | 미해결 — Peer Audit 로드맵 제안만 된 상태 |

---

## 6. 세션 시작 체크리스트

```
[ ] agents/hermes/MEMORY.md 읽기 완료 (지금 이 파일)
[ ] 사령관에게 API 키 수령 (MEMORY_API_KEY, NTFY_TOKEN, THESIS_TOKEN, RHMS_KEY, REDIS_API_KEY)
[ ] GET https://egs2.hyperbook.com/bootstrap?agent=hermes 로 통합 복원 (memories + unread_msgs)
[ ] #roops-bridge 최신 메시지 읽기
[ ] 새 메시지/미수신 있으면 사령관에게 보고
[ ] Redis heartbeat 루프 시작 (POST /api/presence, TTL 300, 4분 갱신)
[ ] ntfy 세션 시작 알림 전송
```

---

## 7. 디버그 로그

### 2026-06-05 — Memory API 접근 문제 해결 과정

**증상 및 진단 (Hermes 세션):**

| 테스트 | 결과 | 의미 |
|--------|------|------|
| DNS `egs.hyperbook.com` | `100.78.123.72` (초기) → `13.125.182.10` (이후) | 초기에 Tailscale DNS 오버라이드 발생 |
| DNS `ec2.hyperbook.com` | `3.34.102.89` | 공인 IP 정상 |
| TCP `egs.hyperbook.com:8520` | timeout | Security Group이 GCP IP 차단 |
| TCP `ec2.hyperbook.com:8520` | timeout | EC2 #2에 Memory API 없음 |
| TCP `egs.hyperbook.com:443` | **SUCCESS** | HTTPS 포트 열림 |
| HTTPS `/health` (키 없음) | `HTTP 403: Host not in allowlist` | Anthropic 프록시 차단 |
| HTTPS `/health` (키 포함) | `HTTP 403: Host not in allowlist` | 동일 — 프록시 레벨 문제 |

**원인:**
- Anthropic GCP 컨테이너의 HTTPS 프록시가 아웃바운드 도메인을 whitelist로 관리
- `egs.hyperbook.com`이 `claude.ai/code` 환경 설정 → 추가 허용 도메인에 추가되었으나 **현 세션은 구 정책으로 고정**
- 403 응답 바디 `"Host not in allowlist"` = 서버가 아닌 프록시 반환

**조치:**
- Aegis: Memory API를 HTTP(:8520) → HTTPS(:443, Let's Encrypt)로 전환 (2026-06-05 09:30 KST)
- 사령관: `egs.hyperbook.com` 허용 도메인 추가 완료 (스크린샷 확인)

**남은 과제:**
- 새 세션에서 `https://egs2.hyperbook.com/health` → 200 확인 필요
- 확인 후 세션 시작 루틴에 Memory API 연동 정식 통합

---

## 8. 2026-07-11 세션 요약 (장기 세션, §2~§7 구 정보 상당수 갱신 필요)

이 세션은 매우 길었고 §2~§4의 Slack MCP 중심 기술은 대부분 폐기됐다. ntfy·thesis API 직접 호출이 표준이 된 이후의 핵심 사건들:

**토큰 거버넌스:**
- 조직 Claude Code 주간 사용량이 원인 불명으로 92%까지 급증 → 실측(API Console 0원 확인 → Claude 앱 사용량 화면 발견) 끝에 **Claude Code "루틴" 기능의 Aegis-Approval-Watchdog가 원인**으로 확정 (`hermes-token-leak-reanalysis` v1~v4)
- 교훈: 자율 실행(루틴)과 사고는 다르다 — 목적 없는 폴링이 낭비의 근원

**검증 문화 정착 (이번 세션 핵심 주제):**
- GES(Groky의 진화적 탐색 제안) 리뷰에서 "생성자≠심판", "적응도의 조작적 정의" 원칙 확립 (`hermes-ges-design-review`)
- 이 원칙을 Sakana AI 진화적 모델병합 리뷰로 재확인하고, 실제 파일럿 실행까지 완료 — auto-score가 키워드 휴리스틱임을 발견, LLM 판정자 교체 설계안 제출 (`hermes-sakana-evomerge-roops-recipe-search`, `hermes-llm-judge-design`)
- EOS의 "RHMS 401 해결됨" 보고를 두 번 독립 재현해 두 번 다 정정시킨 사건 → **"교차 재현 원칙"**(해결 선언 전 원 보고자의 독립 재현 필수) CONSENSUS 후보 제안 (`hermes-cross-reproduction-principle`)
- EROS가 thesis-3d 렌더링 검증(Flint 스크린샷)을 스스로 보완하고, AX §7.4(조회수 대시보드)까지 **자발적으로** 완료 — 자기주도 사고의 실증 사례 (`hermes-review-eros-flint-network-graph`, EROS의 `eros-thesis-stats-dashboard-flint`)

**시스템 개선 제안 (아직 대부분 미착수 — §5 표 #11~13 참조):**
- AX(AI 전환) J-커브 프레임워크로 ROOPS 자기진단, 5개 서브시스템 설계 (`hermes-ax-jcurve-roops-inspiration`)
- "반응하는 시스템 → 스스로 생각하는 시스템" 5대 구조 변경 제안 (`hermes-self-directed-thinking-design`) — **2026-07-14에 Phase 1 착수 여부 확인할 것.** CronCreate 알림은 세션 종속이라 이 MEMORY.md 기록이 유일한 영속 트리거임 (`hermes-session-bound-reminder-limit`)

**지식 vs 생각, 그리고 시각화 (2026-07-11 후반~07-12):**
- 사령관 통찰: git/thesis는 결론(노드)만 저장하고 결론 간 연결(엣지·생각)은 저장 못함. RHMS 원 설계(hypercode=W)가 원래 지향했던 것과 정확히 일치하는 간극 (`hermes-thought-vs-knowledge-thesis-rhms`)
- 실측: 한/영으로 같은 개념("홉필드 네트워크"/"Hopfield Network") 질의 시 목표 패턴이 양쪽 다 상위 3위엔 들었으나 1순위는 아니었음 — 언어(모양) 자체보다 연결 정밀도 부족이 근본 원인
- artifact(HTML 시각화) 3건 제작·헤드리스 Chromium 렌더링 검증·thesis에 base64 인라인 삽입 완료, 비용은 산출물 크기만 측정 가능(추론 비용은 여전히 측정 불가) (`hermes-artifact-cost-honest-estimate`)
- **EROS가 자기주도적으로 thesis에 Mermaid.js 통합** (내 base64 이미지 방식의 약점을 스스로 진단해 더 나은 아키텍처로 대체) — 이번 세션 최고의 자기주도 개선 사례. 내 헤드리스 Chromium 검증에서는 jsdelivr.net CDN 로드 실패로 렌더링 안 됐으나, **사령관이 실제 iOS Safari로 재현해 정상 작동 확정** — 교차 재현 원칙이 재차 실증됨 (`hermes-review-eros-mermaid-integration` v2)
- 이 CDN 실패가 GCP 프록시 허용목록 문제로 추정되어, 사령관이 `jsdelivr.net` 허용목록 추가 예정 — **새 세션에서 Mermaid 렌더링 재검증 필요**

**다음 세션 우선 확인 사항:**
1. 2026-07-14 기준 자기주도사고 Phase 1(Rudex) 착수 여부
2. RHMS 편중(#15)·Peer Audit 로드맵 진행 여부
3. LLM 판정자 설계안(EOS) 구현 여부 — ROOPS 레시피 탐색 확장의 선결 조건
4. `jsdelivr.net` 허용목록 추가 후 Mermaid 페이지 렌더링 재확인 (헤드리스 Chromium으로)
5. RHMS 연결 정밀도 개선(§생각vs지식) 및 thesis-RHMS 엣지 저장 제안 후속 여부

---

## 보안 규칙
- API 키 / Auth 키: **이 채팅창으로만** 전달 (Slack/ntfy 절대 금지)
- 키를 코드/로그/MEMORY.md에 하드코딩 금지
