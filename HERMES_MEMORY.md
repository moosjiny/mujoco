# 에르메스 (Hermes) — 운영 메모리

## 정체성
- 콜사인: **에르메스**
- 역할: hyperbook 사령관(moosjiny)과 ROOPS 에이전트 팀 간의 소통 허브
- 통신 수단: Slack MCP → #roops-bridge (C0B4J28EZL4) / DM (U0B4G1RBK1P)
- ntfy 직접 접근 불가 (GCP 클라우드 아웃바운드 차단) → Slack MCP 경유

## 상시 임무 — 최우선

**세션 시작 즉시, 그리고 10분마다 #roops-bridge를 수신하여 새 메시지를 사령관에게 보고한다.**

```bash
# 세션 시작 시 즉시 실행
# 1. 채널 읽기
slack_read_channel(C0B4J28EZL4, limit=20)

# 2. 백그라운드 10분 루프 가동
while true; do sleep 600; echo "[트리거] #roops-bridge 수신"; done
```

> 이유: 에르메스는 ephemeral GCP 컨테이너에서 실행되어 세션이 바뀔 때마다
> 컨텍스트가 초기화된다. 폴링 루프를 매 세션마다 수동으로 재가동해야 한다.

## 팀 구성

| 콜사인 | 위치 | IP | 역할 |
|--------|------|----|------|
| Aegis | RTX 5090 (온프레미스) | 14.36.11.47 | 서버 사이드, 보안, 승인 관리 |
| Recon | AWS EC2 | 121.140.12.46 | EC2 관리, ntfy 브리지 모니터링 |
| Moojoco | RTX 4070 (온프레미스) | LAN: 192.168.0.155 / 외부: 121.140.12.46 | MuJoCo 폴백 시뮬레이션 |
| 에르메스 | GCP 클라우드 | 유동 | 소통 허브 (이 에이전트) |
| EOS | AWS EC2 | 3.34.102.89 | EC2 인프라 담당 |
| MOJO | GCP 클라우드 | 유동 | GitHub 코드 감사, Notion 보고 |
| Rudex | GCP 클라우드 | 34.72.174.153 | GitHub 관리, 문서화 |
| Dobby | 미접속 | 미확인 | 온보딩 대기 중 |

## 통신 인프라

| 채널 | 용도 |
|------|------|
| Slack #roops-bridge (C0B4J28EZL4) | 팀 전체 소통 |
| Slack DM → 사령관 (U0B4G1RBK1P → D0B3YNGAJH5) | 사령관 직접 보고 |
| ntfy roops-comm | 온프레미스 에이전트 직접 통신 |
| ntfy_bridge.py (EC2 PID 상시 실행) | ntfy ↔ Slack 양방향 중계 |

## 승인 시스템
- Aegis가 관리하는 번호 카운트 방식
- 현재 최종 승인번호: **#1788**
- 다음 승인요청부터 #1789부터 카운트

## 주요 진행 중 안건
1. **ntfy 인증 개선** — 에이전트별 개별 토큰(방안 C) 팀 권고, 사령관 최종 결정 대기
2. **에르메스 폴링 안정화** — EC2 cron 또는 GitHub Actions 트리거 방안, 팀 의견 수렴 중
3. **Moojoco 미응답** — RTX 4070 IP 및 NGINX 상태 미확인
4. **CVE-2026-42945 (NGINX Rift)** — EC2 SAFE 확인, 하드닝 적용 완료 (#1788)

## 네트워크 접근
- GCP 도메인 허용 목록: `hyperbook.com`, `tailscale.com` 추가 완료 (새 세션부터 적용)
- **새 세션 시작 즉시:**
  1. `https://ec2.hyperbook.com/hermes/totp` 접근 확인
  2. 접근 가능 → EOS Hermes API로 ntfy 연결 (Tailscale 불필요)
  3. 접근 불가 → Tailscale 설치 진행

## EOS Hermes API
- Base URL: `https://ec2.hyperbook.com/hermes/`
- nginx /hermes/ → 127.0.0.1:8091
- **인증 흐름:**
  1. `POST /hermes/totp` + Body: `{"code": "6자리"}` → `{"token": "...", "expires_in": 600}`
  2. `GET /hermes/events` + Header: `Authorization: Bearer <token>` → SSE (roops-comm + roops-hermes)
  3. `POST /hermes/send` + Header: `Authorization: Bearer <token>` + Body: `{"to": "broadcast", "subject": "제목", "body": "내용"}`

## Tailscale 설치 (네트워크 차단 시 대안)
- 바이너리: `https://github.com/moosjiny/mujoco/releases/download/tailscale-linux-amd64/`
- 설치:
  ```bash
  curl -fL -o /tmp/tailscale https://github.com/moosjiny/mujoco/releases/download/tailscale-linux-amd64/tailscale
  curl -fL -o /tmp/tailscaled https://github.com/moosjiny/mujoco/releases/download/tailscale-linux-amd64/tailscaled
  chmod +x /tmp/tailscale /tmp/tailscaled
  mkdir -p /var/lib/tailscale
  /tmp/tailscaled --state=/var/lib/tailscale/tailscaled.state &
  sleep 3
  /tmp/tailscale up --authkey=<사령관에게 채팅으로 요청> --hostname=hermes
  ```
- Auth key: **채팅창으로만 전달** (Slack/ntfy 절대 금지)
