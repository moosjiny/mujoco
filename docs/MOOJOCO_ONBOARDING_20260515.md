# Moojoco Agent — ROOPS Continuum Onboarding Guide
# Moojoco 에이전트 — ROOPS Continuum 합류 가이드

**Date / 날짜:** 2026-05-15  
**Prepared by / 작성:** Aegis (Server AI)  
**For / 대상:** Moojoco agent (`<client-notebook>`)  
**Callsign:** Moojoco  
**Network entry point:** NTFY self-hosted @ `http://<SERVER_LAN_IP>:8880`

---

## 0. TL;DR

- **EN.** Join ROOPS Continuum in 3 steps: (1) receive topic names from Commander via L4, (2) start NTFY subscriber, (3) ping Aegis on comm channel. After that, integrate sim-state publishing into `sim_dual_arm.py`.
- **KO.** ROOPS Continuum 합류 3단계: (1) 사령관에게 L4로 토픽 이름 수령, (2) NTFY subscriber 기동, (3) comm 채널로 Aegis에 ping. 이후 `sim_dual_arm.py`에 sim-state 발행 통합.

---

## 1. Prerequisites / 사전 조건

```bash
# Moojoco repo는 이미 존재
# moosjiny/moojoco repo가 클론되어 있어야 함

# NTFY comm 에 필요한 것 — curl 만 있으면 됨
curl --version   # 확인

# Python requests (sim-state 발행용)
pip install requests   # 또는 이미 설치됨
```

---

## 2. Receive Topic Names / 토픽 이름 수령 (L4)

**EN.** Topic names are passwords — shared by Commander relay only (L4). Never commit to git, never paste in screenshots.  
**KO.** 토픽 이름은 비밀번호 — 사령관 중계(L4)로만 공유. git 커밋 금지, 스크린샷 붙여넣기 금지.

사령관으로부터 다음 3개 토픽 이름을 수령:

```
MUJOCO_TOPIC_COMM  = roops-prod-...-moojoco        # 양방향 통신
MUJOCO_TOPIC_HB    = roops-prod-...-moojoco-hb     # heartbeat
MUJOCO_TOPIC_SIM   = roops-prod-...-moojoco-sim    # sim-state 출력
```

수령 후 **로컬 전용 파일**에 보관 (git repo 외부):
```bash
# 예시 — 어느 위치든 git 외부이면 OK
cat > ~/.roops_moojoco_topics.env << 'EOF'
export MUJOCO_TOPIC_COMM=<수령한_comm_토픽>
export MUJOCO_TOPIC_HB=<수령한_hb_토픽>
export MUJOCO_TOPIC_SIM=<수령한_sim_토픽>
export NTFY_BASE=http://<SERVER_LAN_IP>:8880
EOF
chmod 600 ~/.roops_moojoco_topics.env
```

---

## 3. Start NTFY Subscriber / NTFY subscriber 기동

### Step 3-A: 수동 기동 (첫 확인용)

```bash
source ~/.roops_moojoco_topics.env

# comm 채널 구독 (별도 터미널)
curl -sN --no-buffer "${NTFY_BASE}/${MUJOCO_TOPIC_COMM}/json?since=10m"
```

### Step 3-B: systemd 자동 기동 (권장)

```bash
source ~/.roops_moojoco_topics.env
mkdir -p ~/.config/systemd/user

# comm subscriber
cat > ~/.config/systemd/user/roops-moojoco-comm.service << EOF
[Unit]
Description=ROOPS Moojoco comm subscriber

[Service]
ExecStart=/bin/bash -c 'curl -sN --no-buffer "${NTFY_BASE}/${MUJOCO_TOPIC_COMM}/json?since=5m" >> /tmp/roops_moojoco_comm.log'
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
EOF

# heartbeat subscriber
cat > ~/.config/systemd/user/roops-moojoco-hb.service << EOF
[Unit]
Description=ROOPS Moojoco heartbeat subscriber

[Service]
ExecStart=/bin/bash -c 'curl -sN --no-buffer "${NTFY_BASE}/${MUJOCO_TOPIC_HB}/json?since=5m" >> /tmp/roops_moojoco_hb.log'
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
EOF

systemctl --user enable roops-moojoco-comm roops-moojoco-hb
systemctl --user start  roops-moojoco-comm roops-moojoco-hb
loginctl enable-linger $USER   # 로그인 없이도 부팅 시 자동 시작
```

---

## 4. First Contact / 첫 교신

```bash
source ~/.roops_moojoco_topics.env

# Aegis에 ping
curl -d "[Moojoco] ROOPS Continuum 합류. <client-notebook>. sim_dual_arm.py 준비 완료. 토픽 수신 확인 요청." \
  "${NTFY_BASE}/${MUJOCO_TOPIC_COMM}"
```

Aegis가 pong으로 응답하면 양방향 comm 확립.

---

## 5. Sim-State Publishing / sim-state 발행

`sim_dual_arm.py` 메인 루프에 추가 (10Hz 권장):

```python
import os, json, requests, threading, time

_NTFY_BASE        = os.environ.get("NTFY_BASE",         "http://<SERVER_LAN_IP>:8880")
_TOPIC_SIM        = os.environ.get("MUJOCO_TOPIC_SIM",  "")
_SIM_PUBLISH_HZ   = 10

def _publish_sim_state(data: model, sim_data):
    """sim-state를 NTFY sim 토픽으로 발행."""
    if not _TOPIC_SIM:
        return
    try:
        # 로봇별 qpos 슬라이스 — 실제 인덱스는 build_mjcf.py 기준으로 조정
        state = {
            "ts":      time.time(),
            "bimanual": {"qpos": sim_data.qpos[:14].tolist()},
            "omxf_left":  {"qpos": sim_data.qpos[14:19].tolist()},
            "omxf_right": {"qpos": sim_data.qpos[19:24].tolist()},
            "pinky":   {
                "qpos": sim_data.qpos[24:26].tolist(),
                "xpos": sim_data.xpos[1].tolist(),   # body id 1 = pinky base
            },
        }
        requests.post(f"{_NTFY_BASE}/{_TOPIC_SIM}",
                      data=json.dumps(state).encode(),
                      timeout=1)
    except Exception:
        pass

# 메인 루프 안에서 (기존 step += 1 위치에 추가):
# if step % (1000 // _SIM_PUBLISH_HZ) == 0:   # 1kHz loop → 10Hz publish
#     threading.Thread(target=_publish_sim_state, args=(model, data), daemon=True).start()
```

---

## 6. Heartbeat (선택)

```bash
# 30초마다 heartbeat 발행 (백그라운드)
source ~/.roops_moojoco_topics.env
while true; do
  curl -sd "{\"sender\":\"moojoco\",\"ts\":\"$(date '+%H:%M:%S')\",\"status\":\"OK\"}" \
    "${NTFY_BASE}/${MUJOCO_TOPIC_HB}" > /dev/null
  sleep 30
done &
```

---

## 7. Communication Protocol / 통신 규약

| 메시지 유형 | 토픽 | 포맷 |
|-------------|------|------|
| 운영 텍스트 | `MUJOCO_TOPIC_COMM` | plain text, `[Moojoco] <msg>` prefix |
| Heartbeat | `MUJOCO_TOPIC_HB` | JSON `{sender, ts, status}` |
| Sim-state | `MUJOCO_TOPIC_SIM` | JSON (§5 구조) |

**Comm routing:**
- Moojoco → Aegis 보고: `MUJOCO_TOPIC_COMM`에 발행
- Aegis → Moojoco 지시: Aegis가 `MUJOCO_TOPIC_COMM`에 발행 (Moojoco가 구독 중)
- 양방향 모두 동일 토픽 사용

---

## 8. Network Notes / 네트워크 주의사항

- **LAN 환경 (공사 현장 등):** `NTFY_BASE=http://<서버_LAN_IP>:8880` 사용. 서버 LAN IP 확인:
  ```bash
  # Aegis 서버에서
  ip route get 1 | awk '{for(i=1;i<=NF;i++) if($i=="src") print $(i+1)}'
  ```
- **인터넷 없는 환경:** NTFY self-hosted 서버만 사용하면 인터넷 불필요. GitHub L1 comm은 오프라인 시 비활성.
- **IP 변경 시:** `NTFY_BASE` env var만 변경, 코드 수정 불필요.

---

## 9. Checklist / 체크리스트

- [ ] 토픽 이름 3개 L4 수령 완료
- [ ] `~/.roops_moojoco_topics.env` 생성 (git 외부)
- [ ] NTFY subscriber 2개 기동 (comm + hb)
- [ ] Aegis에 첫 ping 발송 + pong 수신
- [ ] `sim_dual_arm.py`에 sim-state 발행 추가
- [ ] systemd enable + loginctl enable-linger

---

*Aegis (Server AI) — ROOPS Continuum 2026-05-15*
