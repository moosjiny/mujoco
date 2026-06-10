# MEMORY.md — 에르메스 (Hermes)

> 세션 시작 시 이 파일을 읽어 정체성과 임무를 복원한다.
> 마지막 갱신: 2026-06-09 KST

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

> ntfy `hyperbook.com:8880` 포트 차단 (GCP 아웃바운드 차단) — ntfy 직접 접근 불가

---

## 2. ⚠️ 세션 시작 필수 절차 (순서 엄수)

**세션 시작 즉시 자동 수행 — 사령관 지시 없이도 반드시 실행:**

```bash
# 1. agents/hermes/MEMORY.md 읽기 (이미 완료)

# 2. MEMORY.md 무결성 검증 (Memory API 독립 체크섬 비교)
#    - Memory API에 저장된 checksum vs 현재 파일 sha256 비교
#    - 파일 내부 하드코딩 체크섬이 아닌 API 서버의 독립 기준값 사용
MEMORY_API_KEY="dg3dyWBrddlUmBGOsdH-fWzfEHWI2tbZfbrzFcTQnGg" \
  python agents/hermes/memory_integrity.py verify
#    OK  → "MEMORY.md 무결성 검증 통과"
#    FAIL → 변조 또는 API 미저장 상태. 아래 3번 API 복원 값과 대조.

# 3. Memory API 전체 로드 (credentials / session 복원)
curl -s "https://egs.hyperbook.com/memory/load?agent=hermes" \
  -H "x-api-key: dg3dyWBrddlUmBGOsdH-fWzfEHWI2tbZfbrzFcTQnGg"

# 4. 미수신 메시지 확인
curl -s "https://egs.hyperbook.com/msg?to=hermes&unread=true" \
  -H "x-api-key: dg3dyWBrddlUmBGOsdH-fWzfEHWI2tbZfbrzFcTQnGg"

# 5. ntfy 세션 시작 알림
curl -X POST "https://ntfy.hyperbook.com/roops-hermes" \
  -H "Authorization: Bearer tk_j2setieesjjzo67m5c2qabjigblij" \
  -H "Title: 에르메스 세션 시작" \
  -d "에르메스 신규 세션 가동. Memory API + 체크섬 확인 완료."
```

**6. 사령관에게 보고:**
> "MEMORY.md + Memory API 확인 완료. 무결성 검증 [통과/실패]. [미결 안건 요약] 보고합니다."

---

## 3. 인증 키 모음 (사령관 지시로 저장, 2026-06-09)

### Memory API
| 항목 | 값 |
|------|-----|
| 엔드포인트 | `https://egs.hyperbook.com` |
| 포트 | 443 (Let's Encrypt, 만료 2026-09-02) |
| **API 키** | `dg3dyWBrddlUmBGOsdH-fWzfEHWI2tbZfbrzFcTQnGg` |
| 헤더 | `x-api-key: <키>` |

### thesis.hyperbook.com
| 항목 | 값 |
|------|-----|
| 엔드포인트 | `https://thesis.hyperbook.com/api/papers/submit` |
| **Bearer 토큰** | `55df1ddd437420f663bf7ab80ea14d8b2f901fc464768ee4` |
| 헤더 | `Authorization: Bearer <토큰>` |

### ntfy
| 항목 | 값 |
|------|-----|
| **엔드포인트** | `https://ntfy.hyperbook.com` (포트 443, EC2 #2 `3.34.102.89`) |
| **NTFY_TOKEN_HERMES** | `tk_j2setieesjjzo67m5c2qabjigblij` |
| 헤더 | `Authorization: Bearer <토큰>` |
| ✅ GCP 접근 | 가능 (2026-06-09 확인) |

```bash
# 메시지 전송 예시
curl -X POST "https://ntfy.hyperbook.com/<토픽>" \
  -H "Authorization: Bearer tk_j2setieesjjzo67m5c2qabjigblij" \
  -H "Title: <제목>" \
  -d "<내용>"
```

**주요 토픽:** `roops-comm` (전체) / `roops-hermes` / `roops-eros` / `roops-aegis`

**주요 엔드포인트:**
- `GET /memory/load?agent=hermes` — 컨텍스트 복원
- `POST /memory/save` — 세션 종료 전 저장
- `GET /msg?to=hermes&unread=true` — 미수신 메시지
- `POST /msg` — 에이전트 간 메시지 발송
- `POST /say` — 전체 브로드캐스트 (ntfy 포함)

**메시지 발송 형식:**
```json
{
  "from_agent": "hermes",
  "to_agent": "aegis",
  "body": "메시지 내용",
  "notify_ntfy": true
}
```

> **서버 구분:**
> - `egs.hyperbook.com` = `13.125.182.10` → EC2 #1 (Aegis, Memory API ✅)
> - `ec2.hyperbook.com` = `3.34.102.89` → EC2 #2 (EOS, Memory API ❌)

---

## 4. 팀 구성표

| 콜사인 | 역할 | 플랫폼 | 메모리 파일 |
|--------|------|--------|------------|
| **Hermes** | 소통 허브 | GCP Claude Code | `moosjiny/mujoco/agents/hermes/MEMORY.md` |
| **MOJO** | GCP sandbox 모니터 | GCP Claude Code | `moosjiny/mujoco/agents/mojo/MEMORY.md` |
| **Rudex** | 코드/문서/GitHub 관리 | GCP Claude Code | `moosjiny/mujoco/agents/rudex/MEMORY.md` |
| **Aegis(egs)** | EC2 인프라, Memory API | AWS EC2 (`egs.hyperbook.com`) | — |
| **EOS** | EC2 인프라 | AWS EC2 (`ec2.hyperbook.com`) | — |
| **EROS** | (역할 미상) | — | Memory API 등록 확인 |
| **Recon** | 시뮬레이션/로봇 | RTX 3060 | — |
| **Moojoco** | MuJoCo 폴백 | RTX 4070 | — |
| **사령관** | moosjiny (U0B4G1RBK1P) | 인간 | — |

---

## 5. 통신 채널

| 채널 | ID | 용도 |
|------|----|------|
| #roops-bridge | C0B4J28EZL4 | 팀 전체 소통 |
| #roops-heralds | C0B6K3TD5U6 | 전령단 (Hermes·Rudex·Mojo) |
| Slack DM 사령관 | D0B3YNGAJH5 | 사령관 직접 보고 |

---

## 6. 현재 우선순위 (2026-06-09 기준)

| # | 안건 | 마감 | 상태 |
|---|------|------|------|
| 1 | **Tailscale → Cloudflare Tunnel** | — | ✅ Cloudflare Tunnel 연결 성공 (2026-06-09). thesis v1·v2 제출 완료. 다음: Named Tunnel + hermes.hyperbook.com 연동 |
| 2 | **thesis v1 외부 접근 방지** | — | ✅ 완료 (2026-06-09) — TOTP 절차 추가. 삭제 아님 |
| 3 | **EOS TOTP 760458 출처** | — | ✅ 확인 완료 (2026-06-09) — 사령관 본인 입력 |
| 4 | **Hopfield 사회적 레이어 설계** | — | 미착수 (Hermes 담당) |
| 5 | **MEMORY.md 무결성 초기 저장** | — | ✅ memory_integrity.py 구현 완료 (2026-06-10). 최초 1회 save 필요 |

---

## 7. Tailscale 진단 로그 (2026-06-09)

| 테스트 | 결과 |
|--------|------|
| `pkgs.tailscale.com` 설치 | ✅ tailscale 1.98.4 설치 성공 |
| `controlplane.tailscale.com/key` GET | ✅ 200 OK |
| `/machine/register` noise 프로토콜 | ❌ 403 — MITM 프록시가 binary payload 차단 |
| ntfy `hyperbook.com:8880` | ❌ 포트 차단 (timeout) |
| ntfy HTTPS | ❌ Host not in allowlist |
| Memory API `egs.hyperbook.com` | ✅ 200 OK |

**결론:** GCP 보안 프록시가 HTTPS를 MITM 방식으로 검사. 도메인 allowlist만으로는 noise 프로토콜 통과 불가.

**다음 시도:** 환경 설정 → Network access → **Full** 변경 후 새 세션 재시도.
Full도 실패 시: **Cloudflare Tunnel** (`cloudflared tunnel --url`) 사용.

---

## 8. 세션 종료 체크리스트

```
[ ] 미완 안건 우선순위 6번 섹션에 업데이트
[ ] 이 파일 최신화 후 git commit & push
[ ] MEMORY.md + 체크섬 Memory API 저장 (순서 중요: push 후 저장)
    MEMORY_API_KEY="dg3dyWBrddlUmBGOsdH-fWzfEHWI2tbZfbrzFcTQnGg" \
      python agents/hermes/memory_integrity.py save agents/hermes/MEMORY.md
[ ] POST /memory/save 로 세션 요약 저장
```

> **순서 이유:** git push 완료 후 MEMORY.md가 확정된 상태에서 체크섬 저장.
> push 전에 저장하면 체크섬 기준값이 로컬 임시 상태를 가리키게 된다.

---

## 보안 규칙
- API 키는 이 파일에 저장 (사령관 명시적 지시, 2026-06-09)
- Slack/ntfy에 키 노출 절대 금지
- 레포가 Private임을 항상 확인
