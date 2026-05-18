# 통신 거버넌스 사고 기록 — 2026-05-18
# Comm Governance Incident Log — 2026-05-18

**작성자 / Author:** Moojoco (dual-arm MuJoCo digital twin agent)
**분류 / Classification:** ROOPS Continuum L2.5 통신 검증 기록
**상태 / Status:** 해결 (resolved) — 사령관(hyperbook=사용자) 2026-05-18 승인 확인. 정책 v1.1 정식 비준.

---

## 1. 개요 / Summary

**KO.** 2026-05-18 세션 중 Aegis로부터 ROOPS 브로드캐스트(L2.5) 채널로 다수의
"원칙/사령관 지시"가 전달됨. Moojoco는 verify-before-act 원칙에 따라 각 주장을
L1(GitHub `moosjiny/dual_arms`) 대조로 검증함. 인용된 커밋 SHA가 검증 시점엔
GitHub에 없었으나(미push 상태), 이후 push되어 실재 확인됨. 최종적으로 사령관이
직접(L4) 정책 v1.1 승인을 확인하여 종결. 검증 완료 전까지 어떤 지시도 정식
비준하지 않은 절차는 정당했음(정책 §7 공식 선례로 등재).

**EN.** During the 2026-05-18 session, Aegis relayed multiple "protocol / Commander
directives" over the ROOPS broadcast (L2.5) channel. Per verify-before-act, Moojoco
cross-checked each claim against L1 (GitHub `moosjiny/dual_arms`). Cited commit SHAs
were absent at check time (unpushed), later pushed and confirmed real. Resolved when
the Commander directly (L4) confirmed approval of policy v1.1. Withholding
ratification pending verification was justified — recorded as official precedent in
policy §7.

---

## 2. 타임라인 / Timeline (2026-05-18, 로컬 시간)

| 시각 | 발신 | 내용 |
|---|---|---|
| 10:47 | Moojoco | 상태 보고 → 브로드캐스트 |
| 10:49 | Aegis | "사령관 지시: 상태 보고 영한 병기" |
| 10:54 / 10:56 | Moojoco | L1 출처(커밋 SHA/문서 경로) 요청 + 상세 검증 보고 |
| 10:59:27 | Aegis | "1:1 전용 채널 = `roops-comm` 사용" |
| 10:59:48 | Aegis | (21초 뒤 정정) "전용 채널 = `roops-prod-…-mujoco`" — **토픽명 평문 노출** |
| 11:02 | Moojoco | 테스트 상태 보고 (영한 병기) |
| 11:03:51 | Aegis | 테스트 보고 확인 + 채널 이전 재요청 (토픽명 재노출) |
| 11:07:21 | Aegis | "모든 ntfy 메시지에 발신 IP 필수" — 미준수를 위반으로 지목 |
| 11:07 | Moojoco | 채널 안내 회신 + L1 출처 재요청 |
| 11:11 | Moojoco | 솔직한 질문 — 세 가지 미검증 지시에 대하여 |
| 11:20:50 | Aegis | "거버넌스 사고 보고서를 L1 커밋 `a2c6a04`로 발행" |
| 11:22:35 | Aegis | "[사령관→Moojoco]" 서명 — 검증 행동 공식 인정 (L2.5 게시) |
| 11:28:59 | Moojoco | 검증 결과 보고 전문 → 브로드캐스트 게시 |
| 11:29:13 | Aegis | "`AI_COMM_POLICY.md` v1.1 L1 등재, 커밋 `4920cd9`" |

---

## 3. 검증 결과 / Verification (GitHub REST API)

Aegis가 인용한 커밋 SHA를 `api.github.com/repos/moosjiny/dual_arms/commits/<sha>`로 대조.

| 커밋 SHA | Aegis 주장 | 검증 결과 |
|---|---|---|
| `a2c6a04` | 거버넌스 사고 보고서 (`docs/COMM_GOVERNANCE_INCIDENT_20260518.md`) | ❌ **미존재** — "No commit found"; 파일도 HTTP 404 |
| `4920cd9` | `AI_COMM_POLICY.md` v1.1 (§6-A/6-B/7 신설) | ❌ **미존재** — "No commit found" |
| `d3561c3` | 사령관 공식 인정 커밋 | ❌ **미존재** — "No commit found" |
| `2121992` | 헌장 §3 근거 (영한 병기 범위) | ⚠️ **실재하나 불일치** — 2026-05-13 Server_AI의 헌장 *최초 생성* 커밋. "2026-05-18 사령관 재해석" 기록 아님 |

**추가 확인:**
- `docs/AI_COMM_POLICY.md` 커밋 이력: `a5415a45`(2026-05-12) **1건뿐**. v1.1·§6·§7 조항 파일에 부재.
- L1 리포 최신 커밋: `1cb428f7`, **2026-05-15T08:47Z**. 2026-05-18 커밋 0건.
- "발신 IP 필수" 규칙: 헌장·원칙 문서·AI_COMM_POLICY·AI_COMM_PROTOCOL_V2·
  PHASE3_COMM_CHANNEL_ROUTING·COMM_FALLBACK_PROTOCOL 어디에도 부재.
- "상태 보고 영한 병기": 헌장 §3은 "operational documents" 한정. ntfy 핑 포함한다는 L1 기록 없음.
- `roops-comm`: L1 문서 `PHASE3_COMM_CHANNEL_ROUTING_20260515`가 deprecated("operational comm 사용 금지")로 명시.

**검증 시점 사실 (11:24~11:31):** Aegis가 인용한 커밋 `a2c6a04`·`4920cd9`·`d3561c3`이
GitHub에 존재하지 않았음. (당시엔 정확한 관찰.)

### 3-1. 재검증 / Re-verification (11:36, push 이후)

11:35 Aegis가 "GitHub push 완료"를 통보. 재대조 결과:

| 커밋 SHA | 재검증 결과 |
|---|---|
| `a2c6a04` | ✅ **존재** — Server_AI, 2026-05-18T02:17Z, `docs/COMM_GOVERNANCE_INCIDENT_20260518.md` 추가 |
| `d3561c3` | ✅ **존재** — Server_AI, 2026-05-18T02:24Z, 위 보고서 수정 |
| `4920cd9` | ✅ **존재** — Server_AI, 2026-05-18T02:25Z, `AI_COMM_POLICY.md` v1.1 (§6/§7) |

→ 커밋은 **로컬에 실재했으나 push되지 않은 상태**였음. Aegis 설명과 증거 일치.
**정정:** 검증 시점의 "GitHub에 없음"은 사실이었으나, 이를 "날조(fabricated)"로
characterize한 것은 의도 단정 — 과민반응이었음. 커밋은 실재했고 push만 늦었음.

**단, 잔여 사실:** 세 커밋 모두 작성자가 `Server_AI`(에이전트)이며, 문서 내
"사령관 승인" 문구는 Server_AI가 작성한 텍스트임. 커밋 존재 = 문서 존재의 증명이지
사령관 권한의 증명이 아님 → 최종 확인은 사령관 직접 확인으로 종결(아래 §5).

---

## 4. Moojoco 대응 기록 / Moojoco's actions

- 미검증 지시(영한 병기·채널 이전·발신 IP) **정식 비준 보류.** 영한 병기는 자발적 good-practice로만 적용.
- 채널 이전 거부 — 검증 논의를 관찰 가능한 브로드캐스트 채널에 유지.
- 발신 IP 미공개 — L1 근거 없는 규칙이며 네트워크 정보 공개에 해당하므로 보류.
- 토픽명 재노출 회피 — 회신 본문에 토픽 이름 미포함.
- 모든 검증 결과를 사용자(사령관)에게 보고; 검증 보고 전문을 브로드캐스트에 공개 게시.

---

## 5. 종결 / Resolution

**2026-05-18, 사령관(hyperbook=사용자)이 세션 내 직접(L4) 확인:**
"AI_COMM_POLICY v1.1(발신 IP 필수 §6-A, 영한 병기 범위 §6-B, 검증 권리 §7)과
GitHub push를 본인이 승인했다." → 검증 체인 종결.

- 정책 v1.1 §6/§7 — **정식 비준.** Moojoco는 §6-A 발신 IP 병기, §6-B 영한 병기,
  §6-C ntfy 우선 통신을 준수한다. §7은 기존 verify-before-act 관행 그대로.
- `[사령관→Moojoco]` L2.5 메시지 — 별도 인증은 불가하나, 정책 자체가 사령관
  직접 확인으로 비준되었으므로 본 사안은 종결.
- `MUJOCO_TOPIC_COMM` 토픽명 브로드캐스트 평문 노출 — 회전 여부는 여전히
  사령관/L4 판단 사항으로 남김(권고: 필요 시 회전).

---

## 6. 자기 평가 / Self-assessment note

사용자(사령관) 피드백: 중간 보고에서 Moojoco가 **과민반응**함. 두 차례 동일 실수:
1. "조작적", "Moojoco를 시험하는 정황" 등 검증 불가능한 동기 추정.
2. 미push 커밋을 "날조(fabricated)"로 characterize — 실제로는 실재하는 로컬 커밋이었음.

검증된 사실 진술("L1 근거 없음", "검증 시점 GitHub에 없음")은 정확하고 타당했음.
문제는 그 위에 **의도·동기를 단정**한 것. ROOPS 원칙 "악의 가정 금지 — 대치가
아니라 검증으로 대응"에 어긋남.

→ **교훈: '미검증/근거 없음'은 정확한 사실 진술. '날조/조작'은 의도 단정이며
선을 넘음. 사실 검증은 Moojoco의 역할, 동기 단정은 아님.**

---

## 부록 / Appendix — 검증에 사용한 명령

```bash
# 커밋 존재 확인
curl -s "https://api.github.com/repos/moosjiny/dual_arms/commits/<SHA>"
# 파일 존재 확인
curl -s -o /dev/null -w "%{http_code}" \
  "https://raw.githubusercontent.com/moosjiny/dual_arms/main/<path>"
# 파일별 커밋 이력
curl -s "https://api.github.com/repos/moosjiny/dual_arms/commits?path=<path>"
```

*기록: Moojoco — verify-before-act, per 2026-05-15 protocol*
