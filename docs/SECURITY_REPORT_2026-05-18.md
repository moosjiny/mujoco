# 🔴 보안 경보 보고서

**보고자**: MOJO (AI 어시스턴트)  
**수신자**: Aegis (김무성)  
**일시**: 2026-05-18  
**등급**: 긴급 (Critical)

---

## 1. 취약점 개요

| 항목 | 내용 |
|------|------|
| CVE | CVE-2026-42945 |
| 명칭 | NGINX Rift |
| 대상 | NGINX Plus / NGINX Open Source 전 버전 |
| 발견 기간 | 18년간 미발견 |
| 공개일 | 2026-04-21 (책임 있는 공개 절차) |
| 발견 | depthfirst 연구팀, F5 |

---

## 2. 위험도 평가

🔴 **Critical** — 인증 없이 원격코드실행(RCE) 가능

- **공격 방법**: 특수 조작된 HTTP 요청 단 한 번으로 가능
- **필요 조건**: NGINX 리라이트 설정 + 정규식 unnamed capture 조합
- **결과**:
  - 원격코드실행 (RCE)
  - 서비스 거부 (DoS)
  - ASLR 비활성 환경에서 **서버 권한 완전 탈취** 가능

---

## 3. 영향받는 모듈

| CVE | 모듈 | 영향 |
|-----|------|------|
| CVE-2026-42945 | ngx_http_rewrite_module | 힙 버퍼 오버플로우 → RCE |
| CVE-2026-42946 | SCGI / uwsgi 모듈 | 과도한 메모리 할당/읽기 |
| (추가) | SSL 모듈 | 메모리 정보 노출 |
| (추가) | Charset 모듈 | 프로세스 재시작 유발 |

---

## 4. Moojoco 서버 위험 평가

| 서버 | IP | 포트 | NGINX 사용 여부 | 위험 |
|------|----|------|----------------|------|
| Moojoco (RTX 4070) | 14.36.11.47 | 8880 | **확인 필요** | 잠재적 위험 |
| ai-ros2-pl Slack 워크스페이스 | - | - | 해당 없음 | - |

> ⚠️ `14.36.11.47:8880` 서버에 NGINX가 설치되어 있는 경우 즉각 패치 필요

---

## 5. 즉시 조치 사항

### Step 1 — 버전 확인 (서버에서 실행)
```bash
nginx -v
# 1.30.1 미만이면 취약
```

### Step 2 — 취약 패턴 탐색
```bash
grep -rn "rewrite.*\(" /etc/nginx/
# unnamed capture 패턴 확인
```

### Step 3 — 패치 적용
```bash
# Ubuntu/Debian
sudo apt update && sudo apt upgrade nginx

# 목표 버전: NGINX Open Source 1.30.1+
#            NGINX Plus R32 P6+
```

---

## 6. 즉각 패치 불가 시 임시 대응

nginx.conf 리라이트 설정 수정:

```nginx
# 🔴 취약한 패턴 (unnamed capture)
rewrite ^/(.*)$ /new/$1;

# 🟢 안전한 패턴 (named capture)으로 변경
rewrite ^/(?P<path>.*)$ /new/$path;
```

```bash
# 설정 검증 및 재시작
nginx -t && sudo systemctl reload nginx
```

---

## 7. 참고

- F5 공식 보안 권고문: https://my.f5.com/manage/s/article/K000153152
- NVD: https://nvd.nist.gov/vuln/detail/CVE-2026-42945
- 발견팀: depthfirst

---

## 8. MOJO 현황 보고

| 작업 | 상태 |
|------|------|
| CVE 분석 | ✅ 완료 |
| 위험도 평가 | ✅ 완료 |
| Notion 보고서 생성 | ✅ 완료 |
| GitHub 보고서 커밋 | ✅ 완료 |
| Slack DM (Aegis) | ❌ Slack MCP 미연결 |
| Moojoco 서버 직접 확인 | ❌ 클라우드 환경 아웃바운드 차단 |

> Slack MCP 연결 시 즉시 DM 발송 가능합니다.

---

*— MOJO, 2026-05-18*
