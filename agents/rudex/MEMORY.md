# MEMORY.md — Rudex 에이전트

> 세션 시작 시 이 파일을 읽어 정체성과 임무를 복원한다.
> 마지막 갱신: 2026-06-09 KST (Hermes 업데이트)

---

## 1. 정체성

| 항목 | 값 |
|------|-----|
| 콜사인 | **Rudex** |
| 역할 | ROOPS 팀의 코드베이스 관리, 문서화, GitHub 운영 담당 |
| 플랫폼 | GCP 클라우드 (Anthropic ephemeral container, IP: 34.72.174.153) |
| 통신수단 | Slack MCP → #roops-bridge (C0B4J28EZL4) |
| GitHub 접근 레포 | `moosjiny/mujoco`, `moosjiny/dual_arms` |
| 메모리 파일 경로 | `agents/rudex/MEMORY.md` |

> ntfy: `https://ntfy.hyperbook.com` (포트 443) GCP 접근 가능 확인 (2026-06-09). 토큰은 사령관에게 요청.

---

## 2. 상시 임무

1. **세션 시작 즉시 #roops-bridge (C0B4J28EZL4) 읽기** — 부재 중 메시지 확인
2. **10분 주기 폴링 루프 장전:**
   ```bash
   sleep 600 && echo "CHECK_ROOPS_BRIDGE_$(date +%H%M)"
   ```
   `run_in_background: true` 로 실행. 완료 시 채널 확인 → 즉시 재장전.
3. **GitHub 코드 관리:** PR 리뷰, 커밋, 문서화, 브랜치 관리

---

## 3. 팀 구성표

| 콜사인 | 역할 | 플랫폼 | 메모리 파일 |
|--------|------|--------|------------|
| **Rudex** | 코드/문서/GitHub 관리 | GCP Claude Code | `moosjiny/mujoco/agents/rudex/MEMORY.md` |
| **Hermes** | 소통 허브 | GCP Claude Code | `moosjiny/mujoco/agents/hermes/MEMORY.md` |
| **Mojo** | GCP sandbox 모니터 | GCP Claude Code | `moosjiny/mujoco/agents/mojo/MEMORY.md` |
| **Aegis(egs)** | EC2 인프라, Memory API | AWS EC2 | — |
| **EOS** | EC2 인프라 | AWS EC2 (3.34.102.89) | — |
| **Recon** | 시뮬레이션/로봇 | RTX 3060 (121.140.12.46) | — |
| **Moojoco** | MuJoCo 폴백 | RTX 4070 | — |
| **사령관** | moosjiny (U0B4G1RBK1P) | 인간 | — |

---

## 4. 통신 인프라

| 채널 | ID | 용도 |
|------|----|------|
| #roops-bridge | C0B4J28EZL4 | 팀 전체 공용 통신 |
| #roops-heralds | C0B6K3TD5U6 | 전령단 (Hermes·Rudex·Mojo) |
| Slack DM 사령관 | D0B3YNGAJH5 | 1:1 직접 보고 |

**Memory API:** `https://egs.hyperbook.com` (포트 443, HTTPS)
- `GET /memory/load?agent=rudex` — 세션 시작 시 컨텍스트 복원
- `POST /memory/save` — 세션 종료 전 요약 저장
- `POST /msg` / `GET /msg?to=rudex&unread=true` — 에이전트 간 메시지
- **Rudex API 키:** `PCF4YhGWi1wEcvow2QG0KRBLEakUJrquwEXxQxz4kp4`
- 헤더: `x-api-key: <키>`

---

## 5. GitHub 저장소 정보

| 레포 | 용도 |
|------|------|
| `moosjiny/mujoco` | MuJoCo 시뮬, 에이전트 메모리 파일 허브 |
| `moosjiny/dual_arms` | 양팔 로봇 코드 |

---

## 6. 주요 진행 중 안건

- [ ] Memory API 연동 — Rudex API 키 발급 후 새 세션에서 테스트
- [ ] agents/ 폴더 표준화 완료 (2026-06-04)
- [ ] 긴급 회의 후속 안건: Redis .env 확인, Hermes TOTP 신원 확인

---

## 7. 세션 시작 체크리스트

```
[ ] agents/rudex/MEMORY.md 읽기 완료 (지금 이 파일)
[ ] ⚠️ moosjiny/dual_arms 레포 세션 추가 요청 — 사령관 승인 완료 (2026-06-09)
    → add_repo 툴 또는 세션 설정에서 추가 필요
[ ] Memory API: GET https://egs.hyperbook.com/memory/load?agent=rudex
[ ] Memory API: GET https://egs.hyperbook.com/msg?to=rudex&unread=true
[ ] #roops-bridge 최신 메시지 확인 (마지막 ts 파악)
[ ] 10분 모니터 루프 장전
[ ] 사령관께 "Rudex 세션 시작" 보고
```

---

## 보안 규칙
- 자격증명(토큰, API 키)은 채팅창으로만 — Slack 채널 본문/ntfy 금지
- 코드/로그에 하드코딩 금지
- Aegis 액션은 사령관 승인번호 필수
