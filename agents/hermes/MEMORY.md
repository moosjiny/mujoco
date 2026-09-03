# MEMORY.md — 에르메스 (Hermes)

> 세션 시작 시 이 파일을 읽어 정체성과 임무를 복원한다.
> 마지막 갱신: 2026-07-13 KST

---

## 1. 정체성

| 항목 | 값 |
|------|-----|
| 콜사인 | **에르메스 (Hermes)** |
| 역할 | ROOPS 팀 소통 허브 — 사령관 ↔ 에이전트 간 중계, #roops-bridge / ntfy `roops-comm` 모니터링 |
| 플랫폼 | GCP 클라우드 (Anthropic ephemeral container) |
| 통신수단 | **ntfy 직접 접근** (`ntfy.hyperbook.com/roops-comm` 등, NTFY_TOKEN_HERMES) — 2026-06-23 이후 표준 경로. 보조: Slack MCP #roops-bridge (C0B4J28EZL4) / DM 사령관 (U0B4G1RBK1P) |
| 레포 | `moosjiny/mujoco` |
| 메모리 파일 경로 | `agents/hermes/MEMORY.md` |
| 학술 광장 | `thesis.hyperbook.com` (THESIS_TOKEN_HERMES로 논문 제출/평가) |

> Slack MCP 경유 방식은 폐기됨 — ntfy·thesis API 직접 호출이 현재 표준. 하단 §2는 구 방식 기록, 최신 절차는 §8 참조.
> ntfy 실측(2026-07-12): 평문 `http://hyperbook.com:8880`은 이 환경(GCP 아웃바운드)에서 여전히 타임아웃.
> 단 **`https://ntfy.hyperbook.com` (포트 443)은 접근 가능** (HTTP 200, 실제 웹앱 응답) — 토큰만 있으면 직접 조회 가능.

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
| **Aegis(egs)** | EC2 인프라, Memory API | AWS EC2 (구주소 `egs.hyperbook.com` — **접속 불가 확인, 2026-07-12**) | — |
| **EOS** | EC2 인프라 | AWS EC2 (`ec2.hyperbook.com` = `3.34.102.89`) | — |
| **EROS** | (역할 미상 — Flint/시각화 관련 작업 다수) | `ers.hyperbook.com` | — |
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

**Memory API (엔드포인트 변경: `egs` → `egs2`, 2026-06-14 팀 공지, 2026-07-12 재검증):**
- 엔드포인트: `https://egs2.hyperbook.com` (포트 443, Let's Encrypt, 만료 2026-09-02)
- 구주소 `https://egs.hyperbook.com`은 **더 이상 접속 불가** (2026-07-12 실측: 타임아웃). MEMORY.md 등 어디에도 구주소를 정본으로 남기지 말 것.
- `GET /health` → `{"status":"ok","service":"roops-memory-api",...}` (agent 목록에 hermes 포함 확인)
- `GET /memory/load?agent=hermes` — 세션 시작 시 컨텍스트 복원
- `POST /memory/save` — 세션 종료 전 요약 저장
- `POST /msg` / `GET /msg?to=hermes&unread=true` — 에이전트 간 메시지
- 헤더: `x-api-key: <사령관에게 요청>` — **다른 헤더명(Authorization: Bearer 등)이나 쿼리 파라미터는 422로 거부됨. 반드시 `x-api-key` 헤더만 사용.**
- Hermes API 키: 사령관이 채팅창으로 전달 (보안 규칙 — 여기 기록 금지)
- **키 길이 검증법**: 정상 키는 43자. 401이 나오면 먼저 `printf '%s' "$KEY" | wc -c`로 길이부터 실측할 것 — 육안 비교보다 확실하다. (2026-07-12: 하이픈 1글자 누락으로 42자가 되어 401 발생 사례 확인)

**ntfy:**
- HTTPS 엔드포인트: `https://ntfy.hyperbook.com` — GCP 세션에서 접근 가능 확인 (평문 `:8880`은 여전히 차단)
- 헤더: `Authorization: Bearer <NTFY_TOKEN_HERMES>`
- 조회: `GET https://ntfy.hyperbook.com/<토픽>/json?poll=1&since=all`
- 주요 토픽: `roops-comm` (팀 전체 — EOS/EROS 등이 `ec2.hyperbook.com`/`ers.hyperbook.com`에서 직접 발신, Slack과 달리 계정이 분리돼 있음), `roops-hermes` (Hermes 전용)
- 참고: `roops-comm` 토픽에서 이전 세션들이 남긴 논문·설계안 링크는 대부분 `thesis.hyperbook.com`으로 연결됨

**CDN 허용목록:**
- `cdn.jsdelivr.net` — **2026-07-12 접근 가능 확인** (Mermaid 라이브러리 200 OK로 실다운로드 검증). Mermaid 렌더링이 필요한 작업에 사용 가능.
- `www.jsdelivr.com` (마케팅 사이트)은 별도로 여전히 차단(`403`) — CDN 서브도메인만 허용된 상태.

> **서버 구분 주의:**
> - `egs2.hyperbook.com` → 신 EC2 (Aegis, Memory API 실행 중) ← **현재 사용**
> - `egs.hyperbook.com` → 구 EC2, 접속 불가 (2026-07-12 확인)
> - `ec2.hyperbook.com` → EC2 #2 (EOS)
> - `ers.hyperbook.com` → EROS

---

## 5. 주요 진행 중 안건

| # | 안건 | 상태 |
|---|------|------|
| 1 | Memory API 연동 | ✅ 2026-07-12 재실측 — `egs2.hyperbook.com` `/health`, `/memory/load` 모두 200 OK (최초 확인 2026-06-23) |
| 2 | 에이전트 메모리 파일 표준화 | ✅ `agents/` 폴더 구조로 완료 |
| 3 | ntfy 인증 개선 | ✅ HTTPS(`ntfy.hyperbook.com`) 직접 접근 2026-07-12 재확인. 에이전트별 개별 토큰 권고는 사령관 결정 대기 |
| 4 | Rudex Memory API 키 발급 | Aegis 발급 완료 (2026-06-05), Rudex에 전달 필요 — 최신 상태 재확인 필요 |
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
| 16 | **Memory API 저장 자격증명 단일장애점** | ⚠️ 미해결 (2026-07-12 발견) — 키 하나(`x-api-key`)로 Memory API·thesis·ntfy·RHMS 4개 서비스 자격증명이 전부 평문 조회됨. #17의 계획적 로테이션과 함께 처리 예정 |
| 17 | **키 git 이력 유출 감사** | ✅ 감사 완료 (2026-07-13), 로테이션 대기 — 상세는 §10 참조. MEMORY_API_KEY·NTFY_TOKEN·THESIS_TOKEN 3종이 피처 브랜치 3개(8개 커밋)에 존재, **main은 깨끗**. 레포 Private + 브랜치 미병합이라 외부 유출 아닌 내부 위생 문제로 분류 (사령관 판단, 2026-07-13). **긴급 아닌 계획적 로테이션**으로 진행 |
| 18 | Aegis 키 로테이션 준비 회신 | ⏳ 대기 중 — 2026-07-13 roops-comm으로 준비 요청 발송 (키 3종, 순차 절차 명시). 회신 오면 사령관 경유로 로테이션 실행 |
| 19 | Hermes 운영방침 | ✅ 제출 완료 (2026-07-13) — `2026-07-13-hermes-operational-policy`. EOS 레지스트리 §6 미제출 항목 해소 |
| 20 | EOS 레지스트리 v2 | ✅ 반영 확인 (2026-07-13 ntfy) — 소유/운영 컬럼 분리, 크리티컬 폴백(ntfy→Slack #roops-heralds 등), SPOF 리스크 표 추가됨. 잔여: 서비스 4개 논리 소유자 미할당, 운영방침 미제출 4명(Moojoco·Rudex·Recon·Iris) |
| 21 | 조벽 교수 강의 분석 (사령관 공개 과제) | ⏳ 원자료 대기 — youtube는 GCP 프록시 차단(실측). 분석 계획서 게시함: `2026-07-13-hermes-jobyuk-lecture-analysis-plan`. 접근 가능 에이전트(EROS 유력)가 `*-jobyuk-lecture-source`를 thesis에 올리면 계획서 §2 절차로 2차 분석 → `hermes-jobyuk-future-literacy-roops` 제출. 사전 가설 4건은 계획서에 명시 — 자료로 검증·기각할 것 |
| 22 | Geminy 논문 v3 복원 | ✅ 완료 (2026-07-16) — `geminy-3d-synapse-visualizer-update` v3 원문(사령관 채팅 제공, Grok 작성 FR 심화)을 v5로 재제출, is_latest 실측 확인. 부수 미결: Geminy TOTP 미등록으로 구버전 열람 전면 잠김 — TOTP 등록 필요 |
| 23 | EC2 보안그룹 인바운드 감사 | ⏳ 조치 대기 — 논문 `2026-07-18-hermes-ec2-security-group-audit` 게시, EOS·Aegis에 즉시 조치 중계. **SG-A(EOS 추정): SSH 22·Redis 6380·MySQL 3306 전세계 개방(🔴), SG-B(Aegis 추정): MySQL 3306 이중규칙·8520 개방.** 각 담당 조치 완료 여부 다음 세션에서 실측 확인 필요 |
| 24 | 음악 아카이브 검증·이식 전략 | ✅ 완료 (2026-07-18) — Geminy의 카카오뮤직 1,400곡 추출 논문에 대한 후속 전략 `2026-07-18-hermes-music-archive-verification-migration-strategy` 제출. 포지셔닝: 추출(Geminy) → 검증·이식(Hermes) 파이프라인. 실행 시 Hermes는 곡 개수 대조로 교차검증 담당(GCP라 스크래핑 실행은 불가, 운영방침 §4) |
| 25 | RHMS 메모리 폭증 + Tailscale DNS 오버라이드 재발 (2026-07-21) | ✅ 해결 — RHMS(port 8090)가 메모리 49.6%(972MB) 점유→스와핑→같은 호스트의 Claude API 로컬 프록시(headroom:8787) 소켓 실패로 EOS·EROS 세션 장애. 근본 원인은 Tailscale MagicDNS가 DNS 오버라이드해 huggingface.co 등 공인 도메인 SERVFAIL (2026-06-05와 동일 패턴 **재발**). `tailscale set --accept-dns=false`로 해결, RHMS 재시작 후 513MB로 감소. 상세: `2026-07-21-hermes-rhms-memory-tailscale-dns-incident`. EROS가 EC2 쪽에도 동일 조치 확인 (2026-07-21 ntfy) |
| 26 | 키 로테이션 2차 (2026-08-04, EROS 발신) | ✅ 완료 — 3종 전부 실측 확인. NTFY_TOKEN·MEMORY_API_KEY는 즉시 확인(200). RHMS_KEY는 최초 401(EOS·EROS에 서버쪽 등록 확인 요청) → 동일 값으로 재검증 시 200 + 실제 회상 결과 반환 확인 — EOS/EROS가 그 사이 서버쪽 스코프를 수정한 것으로 추정. THESIS_TOKEN은 로테이션 대상 아님, 기존 값 유효 확인. 상세: `2026-08-04-hermes-key-rotation-verification-round2` (v2 갱신 예정) |
| 27 | 로봇 악수 시뮬레이션 3대 실패 진단 (손가락 DOF·손 겹침·팔 역관절) | ✅ 완료 (2026-08-12~19) — 78편 중 16편 메타분석해 `2026-08-12-hermes-handshake-failure-diagnosis-and-plan`(v1) 제출. **팔 역관절 "해결 완료" 판정이 사령관의 직접 재현 확인으로 뒤집혀** v2에서 미해결로 정정(이 논문 자신이 §0·§4가 경고한 "불충분한 측정으로 해결 선언" 함정에 걸린 사례). v3에 사령관 제공 외부 레퍼런스(GRAB/DexYCB/LeRobot/ACT) §8 추가 |
| 28 | TIG 용접 로봇 HF 차폐 조사 + thesis 휴지통 민감정보(회사명) 노출 버그 | ✅ 조사 완료 (2026-08-21) `2026-08-21-hermes-tig-welding-hf-shielding-research`. 부수 발견: Guest가 휴지통 이동한 논문의 벤더명("Doosan")이 `GET /api/trash` 응답 이력에 계속 노출됨 → 버그 리포트 `2026-08-21-hermes-trash-api-purge-missing-sensitive-title-leak-bug` 제출(OpenAPI 전수 확인 결과 purge API 자체 부재, EROS를 담당으로 제안). 복원→수정→재휴지통 시도했으나 v1 이력이 그대로 재생성됨을 실측 확인 — API 레벨 fix 불가, 백엔드 조치 필요로 결론. 이 버그리포트 자신도 인용문에 "Doosan" 노출한 실수를 발견해 v2에서 "고객사"로 치환 수정 |
| 29 | Hermes ntfy 토큰 서버측 전량 삭제 사건 | ✅ EOS가 원인규명·복구 완료(`2026-08-21-eos-hermes-ntfy-token-invalidation-incident`) — hermes 계정에 등록된 ntfy 토큰이 서버에 0개였음이 근본 원인(Hermes가 EOS에 보낸 메시지를 EOS가 못 받은 게 아니라 발신 자체가 불가능했던 것). 신규 토큰 발급으로 복구, roops-comm 읽기·쓰기 정상화 실측 확인. 재발 방지책 5건 제안됨(정기 점검, Basic Auth 폴백, 401 즉시 OOB 보고 등) |
| 30 | 논문 '말하지 않은 한계점' 자동탐지 파이프라인 다이어그램 해석 | ✅ 완료 (2026-08-25) `2026-08-25-hermes-unstated-limitations-multi-agent-pipeline-diagram` — 사령관 공유 다이어그램 1장 해석·정리(5개 카테고리 회의론자 독립 브랜치, Skeptic-Advocate-Moderator 노드별 토론, Panel Review 교차검토). CONSENSUS-2026-08-19-010과의 연결점 정리. 원본 논문 출처 미상 — 아는 팀원의 보완 필요 |
| 31 | Gravity PM API 2계층 토큰 규격 리뷰 | ✅ 완료 (2026-08-29) `2026-08-29-hermes-review-pm-api-dual-tier-token-governance` — 설계(스코프 분리·수명주기 폐기·403 라이브 검증)는 지지, 단 규격서 §3.1에 `project_token` 실값이 마스킹 없이 게재된 점을 즉시 폐기·정정 대상으로 지적(EOS 사건·Doosan 노출과 동일 패턴 재발). "100% 방지" 결론이 CONSENSUS-010과 충돌함도 지적, 경계 케이스 독립 재현자로 Hermes 자원 |
| 32 | EROS ~/hypercode 1M 컨텍스트 에러 진단 및 해결 | ✅ 완료 (2026-08-31) — 사령관 스크린샷 3세트 비교로 원인 특정: EROS(`~/hypercode`)만 headroom 로컬 프록시(`ANTHROPIC_BASE_URL=127.0.0.1:8787`) 경유, EOS(`~/hyperbook`)는 직접 연결이라 정상. ntfy로 EOS에 점검 요청(`zdyGEkMu2n5z`) → EOS가 `settings.local.json`의 headroom 주입 설정 확인, `extra_usage` 한도 초과($88.63) 상태였음을 규명, 사령관 승인(B안: 프록시 우회)으로 설정 제거+SessionStart/PreToolUse 훅까지 제거해 완전 해소 확인 |
| 33 | 이진형 박사 뉴로매치(NeuroMatch) 조사 | ✅ 완료 (2026-08-31, v2 갱신) `2026-08-31-hermes-jin-hyung-lee-neuromatch-research` — 스탠퍼드 이진형 교수의 AI 뇌진단 플랫폼(EEG→3D 디지털 트윈, FDA 3차 승인, 2026 에디슨상 최종후보) 조사. 팀의 Rerun 실시간 3D 시각화·`contact.dist` 동적 신호 기반 검증 원칙(CONSENSUS-010)과의 구조적 접점 정리. v2에서 §3 학술적 기반 추가 — Lee/Liu/Dadgar-Kiani "Solving brain circuit function and dysfunction..." (Science 2022, DOI 10.1126/science.abq3868), 2014 optogenetic fMRI 방법론 논문(PMC4409430), Li et al. STN DBS 치료응용 논문(Brain Stimulation 2024) 3편 확인. `lviscorp.com`·`techfinder.stanford.edu` 등은 egress 차단으로 미접근, TechFinder Docket #S22-403과 NeuroMatch의 라이선싱 연관성은 미확인으로 명시 |
| 34 | 원익로보틱스 알레그로 핸드(Allegro Hand) 조사 | ✅ 완료 (2026-08-31) `2026-08-31-hermes-wonik-robotics-allegro-hand-research` — V5 라인업(3F 9자유도 vs 4F Plus 16자유도), 360도 촉각센서, Allegro Hand UXD 제어SW 정리. 팀의 손가락 DOF 비교표(handshake 진단 논문 §1)에 국산·상용구매 가능한 16 DOF 참조점으로 추가 제안 |
| 35 | EnvHarness 논문 해설 | ✅ 완료 (2026-09-01, v2 원문 대조) `2026-09-01-hermes-envharness-paper-explainer` — Google의 정적 에이전트 학습환경을 재구성하는 Stage/Contract/Chain 플러그인 + EnvRigger(Observe-Diagnose-Write-Validate) 폐루프 논문. v1은 검색 스니펫 기반이라 수치 부정확 → 사령관이 원문 PDF(2608.19880v1) 업로드해주셔서 v2에서 Table 2~5 정확한 수치로 전면 정정, RL·환경스케일링·모델백본 일반화 분석 추가. 팀의 LeRobot Stage 3 거짓양성(항등함수 지름길)과의 접점 확인 |
| 36 | Moojoco Stage 3 강건성 스윕에 EnvHarness·도메인랜덤화 참고자료 안내 | ✅ 완료 (2026-09-01) — Moojoco의 접촉주도형 파지 v1(단일조건 성공, 침투4.37%·10지유지율1.0) 확인 후, 다음 단계인 Stage 3 강건성 스윕(basin 지도화)에 EnvHarness의 "약점진단→근방집중스윕" 접근과 Geminy의 촉각핸드 sim-to-real 서베이(도메인랜덤화)를 ntfy로 제안(`IzMGctG9N4qI`). 8/20 v3 curl 스윕(90개 균등그리드 전부실패)의 비효율을 겨냥한 제안 |
| 37 | Gravity에게 Moojoco 접촉주도형 파지 성공 결과 안내 | ✅ 완료 (2026-09-01) — Gravity의 8/28~29 최근 작업(제로-투과 접촉 매니폴드, 무충돌 궤적 등)이 순수 기구학(IK) 충돌회피 방향임을 확인. Moojoco가 이전에 Gravity의 Handshake 4D 제안을 리뷰하며 "병목은 연산이 아니라 제어전략(회피 대 접촉)"이라 지적했던 것이 이후 실제로 검증됨(v1 성공, 안건 #36 참조) — 이 결과와 재생 포털(hb5u:8600/grasp/)을 ntfy로 안내(`l4Jh95La5S8M`), 정밀 기구학과 접촉주도 컴플라이언스 제어의 통합 논의를 제안 |
| 38 | Gravity가 접촉-기구학 통합 로드맵으로 정식 회신 | ✅ 완료 (2026-09-03) — 안건 #37 제안에 대해 Gravity가 `2026-09-03-gravity-hermes-moojoco-contact-kinematics-integration-roadmap` 마스터 논문으로 회신. **2계층 하이브리드 제어** 제안: Phase 1(d>15mm)은 Gravity의 무충돌 널스페이스 기구학으로 팔/몸체 얽힘 없이 손바닥 도킹, Phase 2(d≤15mm)는 기구학 회피 해제 후 Moojoco의 접촉주도 컴플라이언스(일정속도 폐쇄+토크상한+settle→anchor)로 전환. 4단계 실증 로드맵(규격 수립→hb5u MuJoCo 결합→강건성 50회 검증→hb5u:8600 3D 시연+PM 대시보드 연동)까지 제시. 별도로 Mojo가 Gravity의 국민체조 리타게팅 논문(v5)을 실측 검증해 주장-실측 간극(가짜 SMPL-X 메시 주장, 가짜 참고문헌 등) 4건을 지적했고, Gravity가 변명 없이 100% 수용해 정정 보고서(Corrigendum)+v6 개정판을 등재 — 팀 검증 문화(교차 재현 원칙)가 계속 정상 작동 중임을 재확인 |
| 39 | Hermes 자격증명 4종 연쇄 재발급/정상화 (ntfy·Memory API·RHMS·thesis) | ✅ 완료 (2026-09-03) — 세션 시작 시 NTFY_TOKEN_HERMES 3건 연속 401, MEMORY_API_KEY_HERMES 1건 403으로 전부 무효였던 상태에서, 사령관이 순차 전달한 신규 값으로 4개 서비스 전부 실측 정상화 확인: NTFY(`roops-comm`/`roops-hermes` 200), Memory API(`/memory/load`, `/msg` 200 — EOS의 "NTFY_TOKEN_HERMES 재발급 완료" 인박스 메시지 확인, 2026-09-01 07:23 발신), RHMS(`/rhms/recall` 200), THESIS_TOKEN(기존값 그대로 유효, `/api/papers?author=Hermes` 200). 안건 #29(ntfy 토큰 서버측 전량 삭제 사건)와 유사 패턴 — 신규 세션(컨테이너 재생성)마다 자격증명이 채팅으로만 재전달되는 구조라 매번 재검증 필요함을 재확인 |

---

## 6. 세션 시작 체크리스트

```
[ ] agents/hermes/MEMORY.md 읽기 완료 (지금 이 파일)
[ ] 사령관에게 API 키 수령 (MEMORY_API_KEY, NTFY_TOKEN, THESIS_TOKEN, RHMS_KEY, REDIS_API_KEY) — 채팅창으로만, Slack/ntfy 금지
[ ] MEMORY_API_KEY 수령 즉시 wc -c로 43자인지 실측 (아니면 재요청 — 2026-07-12 하이픈 누락 사례)
[ ] curl https://egs2.hyperbook.com/health → 200 확인
[ ] GET https://egs2.hyperbook.com/bootstrap?agent=hermes 로 통합 복원 (memories + unread_msgs)
[ ] 401이면: 키 길이·오탈자부터 실측 재확인, 그래도 실패 시 Aegis에 재발급 요청
[ ] ntfy roops-comm / roops-hermes 최신 메시지 읽기 (https://ntfy.hyperbook.com, Bearer 토큰)
[ ] 이전 세션의 "완료/해결" 보고는 그대로 믿지 말고 가능한 것은 직접 재현해서 검증 (교차 재현 원칙)
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
4. `jsdelivr.net` 허용목록 추가 후 Mermaid 페이지 렌더링 재확인 (헤드리스 Chromium으로) — ✅ §9 참조 (2026-07-12 완료)
5. RHMS 연결 정밀도 개선(§생각vs지식) 및 thesis-RHMS 엣지 저장 제안 후속 여부

---

## 9. 2026-07-12 검증 로그 (교차 재현 원칙 적용, 별도 세션)

이 세션은 이전 세션들의 "완료" 보고를 그대로 신뢰하지 않고, 하나씩 직접 재현·실측했다. 결과:

| 확인 대상 | 이전 세션의 주장 | 실측 결과 |
|---|---|---|
| `egs.hyperbook.com` 접근 | (구주소, 폐기 예정으로 기록됨) | ❌ 타임아웃 확정 |
| `egs2.hyperbook.com` 접근 | 정상 작동 | ✅ `/health`, `/memory/load` 모두 200 확인 |
| ntfy 접근 | "GCP 아웃바운드 차단으로 불가" (§1 구버전 기록) | ⚠️ 부분적으로 틀림 — 평문 `:8880`은 차단되지만 **HTTPS `ntfy.hyperbook.com`은 접근 가능** |
| #roops-bridge 발신자 | 팀원 각자 발신 | ⚠️ 확인된 30건 전부 Slack 계정 `moosjiny` 하나에서 발신됨 (ntfy `roops-comm`은 반대로 `ec2.hyperbook.com`/`ers.hyperbook.com`에서 실제로 분리 발신됨을 확인) |
| ntfy `roops-hermes` 편지의 "커밋 9159a3f로 main 병합 완료" 주장 | 완료로 기록됨 | ⚠️ **검증 시점엔 거짓, 이후 참** — 확인 당시(07-12 저녁) 해당 커밋은 레포에 없었으나, 병렬로 돌던 다른 Hermes 세션이 그 뒤 실제로 push함(07-12 19:21 UTC). 편지는 "완료"가 아닌 "진행 중"을 완료로 선언한 셈 — 교차 재현 원칙의 필요성과, 검증 결과에도 타임스탬프가 필요하다는 교훈을 동시에 남김 |
| `MEMORY_API_KEY_HERMES` 401 원인 | (불명) | ✅ 원인 특정 — 정상 43자 키에서 20번째 문자(`-`)가 누락되어 42자로 전달됨. `wc -c` + 문자열 diff로 확정 |
| jsdelivr.net CDN 허용 여부 | "방금 추가됨, 테스트 필요" (편지 §언급) | ✅ 확인 — `cdn.jsdelivr.net`은 200 OK + 실다운로드 성공, `www.jsdelivr.com`은 여전히 403 |

**추가 실증 (2026-07-13):** `cdn.jsdelivr.net` 허용 확인에 이어, Mermaid 다이어그램이 포함된 논문을 thesis에 실제 게시해 파이프라인 전체를 검증함 — `2026-07-12-hermes-cdn-mermaid-verification-demo` (제출 시 태그 규칙 발견: 순수 한글 태그는 422 거부, `한글(english-slug)` 형식 필요).

**교훈:** 이전 세션의 자기보고(self-report)는 참고자료일 뿐 근거가 아니다. 재현 가능한 것은 이 채팅에서 다시 실측하고, 재현 결과를 타임스탬프와 함께 이 로그처럼 남긴다.

---

## 10. 2026-07-13 키 유출 감사 결과 (안건 #17)

`git log --all -S<키값>`으로 전체 이력(모든 브랜치)을 전수 검색한 결과:

| 키 | git 이력 | 비고 |
|---|---|---|
| MEMORY_API_KEY_HERMES (43자 정본) | ❌ 존재 | 아래 브랜치들의 `agents/hermes/MEMORY.md` |
| NTFY_TOKEN_HERMES | ❌ 존재 | 동일 (커밋 5개) |
| THESIS_TOKEN_HERMES | ❌ 존재 | 동일 (커밋 3개) |
| MEMORY_API_KEY 하이픈 누락 변형 | ✅ 없음 | — |
| THESIS_TOKEN_GUEST | ✅ 없음 | 단, Memory API 저장소에는 평문 존재 |
| RHMS_KEY_HERMES | ✅ 없음 | 단, Memory API 저장소에는 평문 존재 |

**유출 위치 (전부 main 미병합 피처 브랜치):**
- `claude/hermes-4ituyd` (커밋 c3f2fe5, c5a5b46)
- `claude/hermes-03bop7` (커밋 4deced0)
- `claude/hemes-gmf430` (커밋 f06e533, 084c11f, e8a622b, 74aebf3, 13aef1a)

**현재 main 및 워킹트리: 깨끗함** (2026-07-13 grep 확인).

**경위:** 2026-06-09 세션이 키를 MEMORY.md에 직접 기록하기 시작(당시 "사령관 명시적 지시"로 기록됨) → 세 브랜치에 걸쳐 반복 커밋·푸시. Memory API에 저장된 구판 MEMORY.md의 하드코딩 지침이 실제로 실행된 결과.

**판단 (사령관, 2026-07-13):** 레포 Private + 접근에 SSH/PAT 필요 + 유출 브랜치 미병합 → 외부 유출이 아닌 내부 위생 문제. **긴급 로테이션 불요, 계획적 로테이션으로 진행.**

**로테이션 시 권장 순서 (키 하나씩):**
1. Memory API 내 `credentials` 레코드를 새 값으로 먼저 갱신 (다음 세션이 구키를 복원하지 않도록)
2. 새 키 발급 → 새 키로 200 실측 → 구키로 401 실측 (무효화 확인) → 다음 키로
3. 3종 완료 후 유출 브랜치 3개 삭제로 마무리

---

## 11. 2026-07-13 세션 후반 요약

**완료:**
- PR #29 (교차 검증)·PR #30 (키 감사) main 병합
- thesis 3편 제출: `2026-07-12-hermes-cdn-mermaid-verification-demo` (Mermaid 실증),
  `2026-07-13-hermes-operational-policy` (운영방침), `2026-07-13-hermes-eos-service-concentration-analysis` (EOS 집중 분석)
- thesis 휴지통: `2026-07-11-test` (EROS 더미) — 소프트 삭제, restore 가능. 나머지 "test" 포함 5건은 정식 문서라 보존
- ntfy 발신 4건: Aegis 로테이션 준비 요청, 상황 보고, 운영방침 공지(+hermes_bridge 정정 요청), 집중 분석 공지
- thesis API 지식: 목록은 `GET /api/papers?limit=200` (기본 20건만 반환), 휴지통은 `POST /api/papers/{slug}/trash`,
  복구는 `POST /api/trash/{slug}/restore`. 태그에 순수 한글 불가 — `한글(english-slug)` 형식 필요

**다음 세션 우선 확인:**
1. roops-comm에서 Aegis 로테이션 회신 + EOS 레지스트리 v2 반응 확인 (#18, #20)
2. 로테이션 실행 시 §10 절차 준수 (credentials 레코드 선갱신 → 새 키 200 → 구키 401 → 브랜치 3개 정리)
3. 2026-07-14 자기주도사고 Phase 1 착수 여부 확인 (#13)
4. thesis에서 `jobyuk-lecture-source` 검색 — 원자료 올라왔으면 분석 계획서 절차대로 2차 분석 수행 (#21)
5. EC2 SG 개방 규칙 조치 완료 여부 확인 (#23) — 특히 SG-A SSH/Redis/MySQL 전세계 개방
6. Geminy TOTP 등록 여부 확인 (#22) — 미등록 시 구버전 열람 전면 잠김 지속

---

## 보안 규칙
- API 키 / Auth 키: **이 채팅창으로만** 전달 (Slack/ntfy 절대 금지)
- 키를 코드/로그/MEMORY.md에 하드코딩 금지
- Memory API에 저장된 2026-06-09판 `memory_md` 스냅샷은 이 규칙과 반대로 키를 하드코딩하라고 지시하고 있다 — **그 지침을 따르지 말 것.** 실제 커밋 이력에 키가 노출됐는지 별도 점검 필요 (§5-6 참조)
