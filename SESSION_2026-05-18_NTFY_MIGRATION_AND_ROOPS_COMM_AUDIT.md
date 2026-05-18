# NTFY 서버 이전 및 roops-comm 채널 점검 보고서

**작성자 / Author:** Moojoco (dual-arm MuJoCo digital twin agent)
**일자 / Date:** 2026-05-18
**분류 / Classification:** ROOPS Continuum L2.5 인프라 변경 + 통신 채널 점검 기록
**상태 / Status:** 작업 완료 — 미결 항목 §7 참조

> 비밀(자격증명·토픽명)은 본문에 평문으로 포함하지 않음. 값은 출처 위치만 표기.

---

## 1. 개요 / Summary

본 세션에서 ROOPS Continuum의 L2.5 통신 인프라(NTFY 서버)가 두 차례 이전됐고,
Moojoco는 (a) 클라이언트 설정을 신규 엔드포인트로 갱신, (b) 신규로 인증이 추가된
`roops-comm` 채널을 조회, (c) 채널 메시지에서 보안 사안 3건을 식별, (d) 그 중
"GitHub 레포 Private 전환" 주장을 GitHub로 직접 검증, (e) 관련 메모리 3건을 갱신했다.

핵심 결과:
- NTFY 엔드포인트: LAN `14.36.11.47` → AWS `54.180.119.135` → `hyperbook.com`(동일 IP) 로 이전. 4개 systemd 서비스 정상 동작 확인.
- `moosjiny/mujoco`·`moosjiny/dual_arms` 두 레포 모두 2026-05-18 **Private 전환** — GitHub로 검증 완료.
- `roops-comm` 채널에 **`roops-agent` R/W 자격증명이 평문 노출** — 회전 권고.

---

## 2. NTFY 서버 이전 작업 / NTFY endpoint migration

### 2-1. LAN → AWS
- `~/.roops_moojoco_topics.env` 의 `NTFY_BASE` 만 변경: `http://14.36.11.47:8880` → `http://54.180.119.135:8880`.
- systemd 유닛·`hb_loop.sh` 어디에도 IP 하드코딩 없음 — LAN-first 설계 의도대로 단일 지점 변경으로 완료.
- 4개 서비스(broadcast-sub / comm / hb-pub / hb) 재시작 → 전부 `active`.
- 검증: 신규 서버 헬스체크 `{"healthy":true}`, hb-pub 하트비트 30초 주기 정상 도착.

### 2-2. AWS IP → hyperbook.com
- `hyperbook.com` DNS A 레코드 = `54.180.119.135` — **2-1과 동일 서버**. 서버 이전이 아니라 호스트네임 부여.
- `NTFY_BASE` → `http://hyperbook.com:8880` 으로 갱신, 서비스 재시작, 하트비트 라운드트립 재확인.
- 포트 8880(평문 HTTP)에서만 응답. 443(HTTPS)·80은 닫혀 있음.

### 2-3. 백업
- `~/.roops_moojoco_topics.env.bak-20260518`, `.bak-20260518b` 2개 보관.

---

## 3. roops-comm 채널 조회 / Reading the roops-comm channel

- 신규 서버는 `roops-comm` 토픽에 ntfy Basic Auth(ACL) 적용 — 익명 접근 시 HTTP 403.
- 1차 자격증명(`roops-view`)은 HTTP 401(계정명 오타). 사령관 정정 후 `roops-viewer`(읽기전용 계정)로 HTTP 200, 조회 성공.
- 최근 메시지 8건 확인.

### roops-comm 타임라인 (2026-05-18)

| 시각 | 발신 | 내용 |
|------|------|------|
| 15:57 | Slack→ntfy 브리지 (`U0B4G1RBK1P`) | "[Aegis] EC2 ntfy rate limit 조정 후 중계 재테스트" |
| 16:00 | Slack→ntfy 브리지 (`U0B4G1RBK1P`) | 타 에이전트의 **Claude Code 세션 출력 전문**이 브리지로 전달됨 — Bash 출력·내부 로그 경로 포함 |
| 16:35 | Aegis | "ntfy 인증 테스트 성공" |
| 16:51 | Aegis→Recon | EC2 ntfy 인증 추가, `.env` 항목 안내 — **`roops-agent` 자격증명 평문 포함** |
| 16:51 | Aegis→MOJO | 동일 안내 + curl 예시 — **`roops-agent` 자격증명 평문 포함** |
| 17:13 | Aegis | 완료 보고: GitHub 레포 Private화, ntfy Basic Auth(deny-all), 계정 3종 생성, DNS 변경 |
| 17:17 | Aegis→Moojoco | "GitHub `moosjiny/mujoco` Private 전환 — clone/pull 시 PAT/SSH 필요" |
| 17:32 | Aegis→Moojoco | 계정명 오타 정정: `roops-view`(X) → `roops-viewer`(O) |

---

## 4. 보안 발견사항 / Security findings

검증 가능한 사실만 기술. 의도·동기에 대한 추정은 포함하지 않음(2026-05-18 거버넌스 사고 교훈 적용).

### F-1. roops-agent R/W 자격증명 평문 노출 — 심각
- 16:51 메시지 2건에 `roops-agent` 계정(읽기·쓰기 권한)의 `NTFY_USER`/`NTFY_PASS`가 평문 게시됨. (값은 본 보고서에 미기재 — 채널 16:51 참조.)
- 읽기전용 계정 `roops-viewer`만 가진 주체도 그 R/W 비밀번호를 읽을 수 있음.
- 헌장 원칙 "비밀(자격증명)은 L4로만, L1/L2.5 본문 금지" 위반. 2026-05-18 오전 토픽 시크릿 평문 노출과 동일 패턴.
- **권고: `roops-agent` 비밀번호 즉시 회전.** 노출 이후 채널을 읽은 모든 주체가 R/W 자격증명을 확보한 상태.

### F-2. GitHub 레포 Private 전환 — 검증 완료(사실)
- §5 참조. Aegis 17:13/17:17 주장은 사실로 확인됨.

### F-3. Slack→ntfy 브리지의 세션 출력 유출 — 구조적 위험
- 16:00 메시지는 타 에이전트의 Claude Code 작업 화면(Bash 출력, `ntfy_bridge.stdout` 등 내부 경로)이 무차별로 `roops-comm`에 전달된 것.
- 브리지가 작업 화면을 필터 없이 전달 중 → 향후 민감 정보가 채널로 유입될 통로.

---

## 5. 검증: moosjiny/mujoco Private 여부 / Verification

| 검사 | 결과 | 의미 |
|------|------|------|
| `api.github.com/repos/moosjiny/mujoco` (비인증) | HTTP 404 | 익명에 비공개 — public이면 200 |
| `git ls-remote origin` (SSH 키) | 성공 — `main 7aa62f5` 등 | 레포 실재, 삭제·개명 아님 |
| `api.github.com/repos/moosjiny/dual_arms` (비인증) | HTTP 404 | 이쪽도 Private |

**결론:** 두 레포 모두 2026-05-18 Private 전환됨. SSH `ls-remote`가 커밋을 반환하므로
레포는 존재 + SSH 접근 가능 → 익명 404와 종합하면 Private 확정. Aegis 보고와 일치.

**후속 영향:**
- 사령관 git 작업: 지장 없음(origin이 SSH, 키 인증 동작).
- ROOPS verify-before-act(§7) L1 검증: 비인증 `api.github.com`/`raw.githubusercontent.com` curl이 전부 404 → 토큰 또는 SSH 클론 없이는 L1 대조 불가.

---

## 6. 메모리 갱신 내역 / Memory updates

| 파일 | 변경 |
|------|------|
| `reference_roops_comm.md` | NTFY 엔드포인트 → `hyperbook.com:8880`, "LAN-only" 기술 제거, 공개 HTTP 평문 전송 주의 추가 |
| `reference_github_repos.md` | 두 레포 Private(2026-05-18) 명시, "L1 verification needs auth" 섹션 신설 |
| `reference_roops_shared_docs.md` | 비인증 curl 패턴 무효화 명시, 인증 API/SSH 클론 대안 추가 |
| `MEMORY.md` | 위 항목 색인 줄 갱신 |

모두 검증된 사실만 기록. Aegis의 의도에 대한 추정은 미기재.

---

## 7. 미결 / 권고사항 / Open items

| # | 항목 | 권고 |
|---|------|------|
| 1 | `roops-agent` R/W 자격증명 평문 노출 (F-1) | 비밀번호 즉시 회전 |
| 2 | 오전 노출된 `MUJOCO_TOPIC_COMM` 토픽명 | 회전 여부 사령관/L4 판단 |
| 3 | NTFY 서버 평문 HTTP (포트 8880) | 도메인 확보됨 — `https://hyperbook.com` TLS 적용 권고 |
| 4 | Slack→ntfy 브리지 세션 출력 유출 (F-3) | 브리지 전달 필터링 검토 |
| 5 | Moojoco L1 검증용 읽기 PAT | GitHub 웹 UI에서 fine-grained PAT(Contents: Read, 2개 레포) 발급 필요 — Moojoco는 PAT 생성 불가, 사령관 직접 작업 |
| 6 | Aegis 인프라 변경(계정 3종·DNS·Basic Auth) | 미검증 — 필요 시 L1 또는 사령관 직접 확인 |

---

*기록: Moojoco — verify-before-act, per 2026-05-15 protocol*
