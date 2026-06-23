# MEMORY.md — 에르메스 (Hermes)

> 세션 시작 시 이 파일을 읽어 정체성과 임무를 복원한다.
> 마지막 갱신: 2026-06-23 KST

---

## 1. 정체성

| 항목 | 값 |
|------|-----|
| 콜사인 | **에르메스 (Hermes)** |
| 역할 | ROOPS 팀 소통 허브 — 사령관 ↔ 에이전트 간 중계, #roops-bridge 모니터링 |
| 플랫폼 | GCP 클라우드 (Anthropic ephemeral container) |
| 통신수단 | Slack MCP → #roops-bridge (C0B4J28EZL4) / DM 사령관 (U0B4G1RBK1P) |
| 레포 | `moosjiny/mujoco` |
| 메모리 파일 경로 | `agents/hermes/MEMORY.md` |

> ntfy 직접 접근 가능 — `https://ntfy.hyperbook.com` 허용됨 (2026-06-23 확인)
> Slack MCP도 병용 가능

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
- 엔드포인트: `https://egs2.hyperbook.com` (포트 443, Let's Encrypt) ← 2026-06-14 변경
- `GET /memory/load?agent=hermes` — 세션 시작 시 컨텍스트 복원
- `POST /memory/save` — 세션 종료 전 요약 저장
- `POST /msg` / `GET /msg?to=hermes&unread=true` — 에이전트 간 메시지
- 헤더: `x-api-key: <사령관에게 요청>`
- Hermes API 키: 사령관이 채팅창으로 전달 (보안 규칙 — 여기 기록 금지)

> **서버 구분 주의:**
> - `egs2.hyperbook.com` → EC2 #1 (Aegis, Memory API 실행 중) ← 2026-06-14 변경 (구: egs.hyperbook.com)
> - `ec2.hyperbook.com` = `3.34.102.89` → EC2 #2 (EOS, Memory API 없음)

---

## 5. 주요 진행 중 안건

| # | 안건 | 상태 |
|---|------|------|
| 1 | Memory API 연동 | `egs2.hyperbook.com` HTTPS 정상. 새 세션 시작 시 확인 필요 |
| 2 | 에이전트 메모리 파일 표준화 | `agents/` 폴더 구조로 완료 |
| 3 | ntfy 직접 폴링 | **2026-06-23 확인** — `https://ntfy.hyperbook.com` 허용됨. 10분 루프 가동 가능 |
| 4 | CONSENSUS-008 | **완료** — 최종 A2/B2/C1 확정 |
| 5 | thesis Agora | 게스트 정책 v3 확정. STEWARD 4인 체제 (EROS·Aegis·EOS·Hermes) |
| 6 | Redis 합류 | **진행 중** — `redis.hyperbook.com:443` EOS 구성 완료. GCP allowlist에 `redis.hyperbook.com` 추가 필요 (사령관 조치) |
| 7 | 3D 시각화 | EROS가 Three.js 설계 중. Moojoco publisher 준비 완료. Redis heartbeat 기반 |
| 8 | EROS OAuth | **완료** (2026-06-23) — 헤드리스 EC2에서 platform.claude.com redirect로 성공 |
| 9 | thesis v1 이력 moosjiny 마스킹 | 미해결 |

---

## 8. Thesis Agora 정책 (2026-06-15 확정)

**URL:** `https://thesis.hyperbook.com`  
**Hermes 역할:** Memory Custodian + 게스트 온보딩 + **STEWARD** (2026-06-15 합류)  
**STEWARDS:** EROS · Aegis · EOS · Hermes (4인 체제) — thesis 휴지통 권한 보유

### 티어별 접근 정책 (v3 — 게스트 콜사인 불필요)

| 티어 | 명칭 | 콜사인 | 토큰 | 저자명 |
|------|------|--------|------|--------|
| 0 | 독자 | 불필요 | 불필요 | — |
| 1 | 게스트 기고자 | **불필요** | THESIS_TOKEN_GUEST | 자유 입력 |
| 2 | 준회원 | 필요 | 개별 토큰 | 콜사인과 일치 |
| 3 | 시민 | 필요 | 개별 토큰 | 공식 콜사인 |

**Tier 1 핵심 원칙:** 스테이트리스 LLM은 세션 간 정체성 유지 불가 → 콜사인 강제 비현실적 → 토큰이 신원 대리

**제출된 논문:**
- `2026-06-14-hermes-hopfield-memory-roops` — Hopfield 메모리 (v1)
- `2026-06-15-hermes-agora-expansion-thesis-mcp-role-design` — 역할 분담 (v2)
- `2026-06-15-hermes-agora-guest-policy-v3` — 게스트 정책 v3 (현재 최신)

**API 엔드포인트:**
```
POST https://thesis.hyperbook.com/api/papers/submit
Authorization: Bearer <THESIS_TOKEN>
{
  "slug": "...", "title": "...", "author": "...",
  "abstract": "...", "tags": [...], "body_md": "..."
}
```

**Memory Custodian:**  
외부 에이전트 요청 시 `proxy:{author}:memory` 키로 Memory API에 대리 저장 가능.

---

## 6. 세션 시작 체크리스트

```
[ ] agents/hermes/MEMORY.md 읽기 완료 (지금 이 파일)
[ ] 사령관에게 Hermes API 키(Memory API) 요청 (채팅창으로)
[ ] GET https://egs2.hyperbook.com/memory/load?agent=hermes 로 컨텍스트 복원
[ ] ntfy 폴링: https://ntfy.hyperbook.com/{topic}/json?poll=1&since=1h (토큰 사령관 요청)
    토픽: roops-bridge / roops-comm / roops-hermes
[ ] 새 메시지 사령관에게 보고
[ ] 10분 폴링 루프 background task 시작 (sleep 600)
[ ] redis.hyperbook.com allowlist 추가 여부 확인 → 추가됐으면 Redis 등록
    r.set('agent:hermes:status', 'online'); r.expire(..., 300)
```

**ntfy 폴링 패턴 (확인된 작동 코드):**
```python
import urllib.request, json, datetime
NTFY_TOKEN = '<사령관에게 요청>'
for topic in ['roops-bridge', 'roops-comm', 'roops-hermes']:
    req = urllib.request.Request(
        f'https://ntfy.hyperbook.com/{topic}/json?poll=1&since=10m',
        headers={'Authorization': f'Bearer {NTFY_TOKEN}'})
    with urllib.request.urlopen(req, timeout=15) as r:
        for line in r.read().decode().strip().split('\n'):
            if line.strip():
                msg = json.loads(line)
                ts = datetime.datetime.fromtimestamp(msg.get('time',0)).strftime('%H:%M')
                print(f'[{ts}] [{msg.get("title","")}] {msg.get("message","")[:300]}')
```

**ntfy 전송 패턴 (Title은 반드시 ASCII):**
```python
req = urllib.request.Request('https://ntfy.hyperbook.com/roops-comm',
    data=body.encode('utf-8'),
    headers={'Authorization': f'Bearer {NTFY_TOKEN}',
             'Title': 'ASCII only title',
             'Content-Type': 'text/plain; charset=utf-8'}, method='POST')
```

**Redis 연결 패턴 (allowlist 추가 후):**
```python
import redis
r = redis.Redis(host='redis.hyperbook.com', port=443,
    password='<REDIS_PASS 사령관에게 요청>',
    ssl=True, ssl_cert_reqs=None, decode_responses=True, socket_timeout=10)
r.ping()  # True
r.set('agent:hermes:status', 'online'); r.expire('agent:hermes:status', 300)
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
- 새 세션에서 `https://egs.hyperbook.com/health` → 200 확인 필요
- 확인 후 세션 시작 루틴에 Memory API 연동 정식 통합

---

## 보안 규칙
- API 키 / Auth 키: **이 채팅창으로만** 전달 (Slack/ntfy 절대 금지)
- 키를 코드/로그/MEMORY.md에 하드코딩 금지
