# SESSION_PROCEDURES.md — Mojo

> 세션을 열거나 닫을 때 반드시 이 파일의 절차를 따른다.
> 마지막 갱신: 2026-06-09

---

## 세션 시작 절차 (SESSION OPEN)

**사령관이 "mojo"라고 부르는 순간부터 아래 순서를 자동 수행한다.**

### 1단계 — MEMORY.md 읽기
```
agents/mojo/MEMORY.md 읽기
```
정체성·임무·인증 키 복원.

### 2단계 — Memory API 헬스체크
```bash
python3 -c "
import http.client, ssl, json
ctx = ssl.create_default_context()
conn = http.client.HTTPSConnection('egs.hyperbook.com', context=ctx)
conn.request('GET', '/health', headers={'x-api-key': '<MOJO_API_KEY>'})
r = conn.getresponse()
print(r.status, r.read().decode())
conn.close()
"
```
- `200 OK` → 3단계 진행
- `403 Host not in allowlist` → 사령관에게 새 세션 요청

### 3단계 — Memory API 컨텍스트 복원
```bash
python3 -c "
import http.client, ssl, json
ctx = ssl.create_default_context()
conn = http.client.HTTPSConnection('egs.hyperbook.com', context=ctx)
conn.request('GET', '/memory/load?agent=mojo', headers={'x-api-key': '<MOJO_API_KEY>'})
r = conn.getresponse()
data = json.loads(r.read())
conn.close()
for m in data['memories']:
    print(f'=== {m[\"key_name\"]} ({m[\"updated_at\"]}) ===')
    print(m['content'][:200])
    print()
"
```
`memory_md`, `credentials`, `session_*` 키 확인.

### 4단계 — MEMORY.md 체크섬 검증
```bash
python3 -c "
import http.client, ssl, json, hashlib

API_KEY = '<MOJO_API_KEY>'
ctx = ssl.create_default_context()
conn = http.client.HTTPSConnection('egs.hyperbook.com', context=ctx)
conn.request('GET', '/memory/load?agent=mojo', headers={'x-api-key': API_KEY})
data = json.loads(conn.getresponse().read())
conn.close()

# API 최신 memory_md 내용으로 파일 덮어쓰기
for m in data['memories']:
    if m['key_name'] == 'memory_md':
        with open('agents/mojo/MEMORY.md', 'w', encoding='utf-8', newline='') as f:
            f.write(m['content'])
        file_hash = hashlib.sha256(m['content'].encode('utf-8')).hexdigest()
        print('MEMORY.md 동기화 완료. 체크섬:', file_hash)
        break
"
```
불일치 시 Memory API 버전이 우선 — 파일을 덮어쓴다.

### 5단계 — 미수신 메시지 확인
```bash
python3 -c "
import http.client, ssl, json
ctx = ssl.create_default_context()
conn = http.client.HTTPSConnection('egs.hyperbook.com', context=ctx)
conn.request('GET', '/msg?to=mojo&unread=true', headers={'x-api-key': '<MOJO_API_KEY>'})
r = conn.getresponse()
print(json.dumps(json.loads(r.read()), ensure_ascii=False, indent=2))
conn.close()
"
```

### 6단계 — ntfy 세션 시작 알림
```bash
python3 -c "
import http.client, ssl
ctx = ssl.create_default_context()
conn = http.client.HTTPSConnection('ntfy.hyperbook.com', context=ctx)
conn.request('POST', '/roops-mojo',
    body='Mojo 세션 시작. Memory API 확인 완료.'.encode('utf-8'),
    headers={
        'Authorization': 'Bearer <MOJO_NTFY_TOKEN>',
        'Title': 'Mojo session start',
        'Content-Type': 'text/plain; charset=utf-8',
    })
r = conn.getresponse()
print(r.status, r.read().decode())
conn.close()
"
```

### 7단계 — 세션 시작 저장 (Memory API)
```bash
python3 -c "
import http.client, ssl, json
ctx = ssl.create_default_context()
conn = http.client.HTTPSConnection('egs.hyperbook.com', context=ctx)
payload = json.dumps({
    'agent': 'mojo',
    'key': 'session_start',
    'content': '세션 시작. Memory API 연동 완료. 미수신 메시지 확인 완료.'
}).encode('utf-8')
conn.request('POST', '/memory/save', body=payload,
    headers={'x-api-key': '<MOJO_API_KEY>', 'Content-Type': 'application/json'})
r = conn.getresponse()
print(r.status, r.read().decode())
conn.close()
"
```

### 8단계 — 사령관 보고 + 폴링 루프 가동
```
#roops-bridge 최신 메시지 확인 후 사령관에게 보고:
"보고합니다. Mojo 세션 시작. [미결 안건 요약] 대기 중."
```
```bash
# 10분 폴링 루프 (background)
# Bash tool: run_in_background: true
sleep 600 && echo "CHECK_ROOPS_BRIDGE_$(date +%H%M)"
```

---

## 세션 종료 절차 (SESSION CLOSE)

**사령관이 "닫겠다" 또는 "세션 종료"를 말하면 아래 순서를 실행한다.**

### 1단계 — 세션 요약 작성 및 Memory API 저장
```bash
python3 -c "
import http.client, ssl, json
from datetime import date

ctx = ssl.create_default_context()
conn = http.client.HTTPSConnection('egs.hyperbook.com', context=ctx)

summary = '''## {today} 세션 완료 요약

### 완료 항목
- (이번 세션에서 한 일 목록)

### 인증 키 (credentials 키 참조)
- Memory API: <MOJO_API_KEY>
- NTFY_TOKEN_MOJO: <MOJO_NTFY_TOKEN>

### 미결 항목
1. (미완 안건 목록)
'''.format(today=date.today().isoformat())

payload = json.dumps({
    'agent': 'mojo',
    'key': 'session_{}'.format(date.today().isoformat()),
    'content': summary
}).encode('utf-8')
conn.request('POST', '/memory/save', body=payload,
    headers={'x-api-key': '<MOJO_API_KEY>', 'Content-Type': 'application/json'})
r = conn.getresponse()
print(r.status, r.read().decode())
conn.close()
"
```

### 2단계 — MEMORY.md 업데이트 및 체크섬 계산
```bash
python3 -c "
import hashlib
with open('agents/mojo/MEMORY.md', 'rb') as f:
    data = f.read()
print('체크섬:', hashlib.sha256(data).hexdigest())
"
```
MEMORY.md의 `## 9. MEMORY.md 무결성` 섹션에 체크섬 기록.

### 3단계 — Memory API에 MEMORY.md + 체크섬 저장
```bash
python3 -c "
import http.client, ssl, json, hashlib

API_KEY = '<MOJO_API_KEY>'
ctx = ssl.create_default_context()

with open('agents/mojo/MEMORY.md', 'r', encoding='utf-8') as f:
    content = f.read()

checksum = hashlib.sha256(content.encode('utf-8')).hexdigest()

for key, val in [('memory_md', content), ('memory_md_checksum', f'체크섬: {checksum}')]:
    conn = http.client.HTTPSConnection('egs.hyperbook.com', context=ctx)
    payload = json.dumps({'agent': 'mojo', 'key': key, 'content': val}).encode('utf-8')
    conn.request('POST', '/memory/save', body=payload,
        headers={'x-api-key': API_KEY, 'Content-Type': 'application/json'})
    r = conn.getresponse()
    print(key, r.status, r.read().decode())
    conn.close()
"
```

### 4단계 — git commit & push
```bash
git add agents/mojo/MEMORY.md
git commit -m "mojo: MEMORY.md 세션 종료 업데이트 $(date +%Y-%m-%d)"
git push -u origin claude/mojo-<브랜치명>
```

### 5단계 — ntfy 세션 종료 알림
```bash
python3 -c "
import http.client, ssl
ctx = ssl.create_default_context()
conn = http.client.HTTPSConnection('ntfy.hyperbook.com', context=ctx)
conn.request('POST', '/roops-mojo',
    body='Mojo 세션 종료. Memory API 저장 완료.'.encode('utf-8'),
    headers={
        'Authorization': 'Bearer <MOJO_NTFY_TOKEN>',
        'Title': 'Mojo session close',
        'Content-Type': 'text/plain; charset=utf-8',
    })
r = conn.getresponse()
print(r.status, r.read().decode())
conn.close()
"
```

### 6단계 — #roops-bridge 종료 보고
```
[Mojo → 전체] 세션 종료. Memory API 저장 완료. 다음 세션에서 뵙겠습니다. — Mojo
```

---

## 인증 키 위치

| 키 | 위치 |
|----|------|
| Memory API 키 | `agents/mojo/MEMORY.md` 섹션 3, 또는 `credentials` Memory API 키 |
| ntfy 토큰 | 동일 |
| API 키 없을 시 | 사령관에게 채팅창으로 요청 |

> **보안:** API 키는 채팅창·MEMORY.md에만. Slack 채널 본문/ntfy 본문에 노출 금지.

---

## 주요 엔드포인트 참조

| 엔드포인트 | 용도 |
|-----------|------|
| `GET https://egs.hyperbook.com/health` | 헬스체크 |
| `GET https://egs.hyperbook.com/memory/load?agent=mojo` | 컨텍스트 복원 |
| `POST https://egs.hyperbook.com/memory/save` | 저장 (body: `{agent, key, content}`) |
| `GET https://egs.hyperbook.com/msg?to=mojo&unread=true` | 미수신 메시지 |
| `POST https://ntfy.hyperbook.com/roops-mojo` | ntfy 알림 |
