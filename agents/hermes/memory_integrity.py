"""
MEMORY.md 무결성 보장 모듈.

저장 시: sha256(MEMORY.md) 계산 → Memory API에 content + checksum 함께 저장
로드 시: API에서 content + checksum 로드 → 독립 비교 → 불일치 시 변조 감지

Memory API 저장 구조:
  POST /memory/save
  { "agent": "hermes", "key": "memory_md", "data": { "content": ..., "checksum": ... } }

  GET /memory/load?agent=hermes&key=memory_md
  → { "content": ..., "checksum": ..., "saved_at": ... }
"""
import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Optional

try:
    import requests as _requests
    _USE_REQUESTS = True
except ImportError:
    import urllib.request as _urllib_request
    import urllib.error as _urllib_error
    _USE_REQUESTS = False

MEMORY_API_URL = "https://egs.hyperbook.com"
MEMORY_MD_KEY = "memory_md"
TIMEOUT = 10
LOCAL_FALLBACK = os.path.expanduser("~/.roops_memory_md_backup.json")


def compute_checksum(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def save_memory_md(content: str, api_key: str) -> dict:
    """
    MEMORY.md 내용과 sha256 체크섬을 Memory API에 함께 저장.
    체크섬은 파일 내부가 아닌 API 서버에 독립적으로 보관된다.
    """
    checksum = compute_checksum(content)
    saved_at = datetime.now(timezone.utc).isoformat()

    payload = {
        "agent": "hermes",
        "key": MEMORY_MD_KEY,
        "data": {
            "content": content,
            "checksum": checksum,
            "saved_at": saved_at,
        },
    }

    _local_backup(payload["data"])

    headers = {"x-api-key": api_key, "Content-Type": "application/json"}

    try:
        if _USE_REQUESTS:
            resp = _requests.post(
                f"{MEMORY_API_URL}/memory/save",
                json=payload,
                headers=headers,
                timeout=TIMEOUT,
            )
            ok = resp.status_code == 200
            detail = resp.text[:120] if not ok else ""
        else:
            body = json.dumps(payload).encode("utf-8")
            req = _urllib_request.Request(
                f"{MEMORY_API_URL}/memory/save",
                data=body,
                headers=headers,
                method="POST",
            )
            with _urllib_request.urlopen(req, timeout=TIMEOUT) as r:
                ok = True
                detail = ""

        if ok:
            print(f"[memory_integrity] 저장 완료. checksum={checksum[:16]}…")
            return {"saved": True, "checksum": checksum, "saved_at": saved_at}
        print(f"[memory_integrity] API 저장 실패: {detail}")
    except Exception as e:
        print(f"[memory_integrity] API 오류: {e}")

    print("[memory_integrity] 로컬 폴백에만 저장됨")
    return {"saved": False, "checksum": checksum, "saved_at": saved_at, "local_only": True}


def load_and_verify_memory_md(api_key: str) -> dict:
    """
    Memory API에서 MEMORY.md + 체크섬 로드 후 독립 검증.

    반환값:
      { "ok": True,  "content": ..., "checksum": ... }          # 검증 성공
      { "ok": False, "reason": ..., ... }                        # 검증 실패 또는 오류
    """
    headers = {"x-api-key": api_key}

    try:
        if _USE_REQUESTS:
            resp = _requests.get(
                f"{MEMORY_API_URL}/memory/load",
                params={"agent": "hermes", "key": MEMORY_MD_KEY},
                headers=headers,
                timeout=TIMEOUT,
            )
            if resp.status_code != 200:
                return {"ok": False, "reason": f"API HTTP {resp.status_code}"}
            data = resp.json()
        else:
            import urllib.parse
            params = urllib.parse.urlencode({"agent": "hermes", "key": MEMORY_MD_KEY})
            req = _urllib_request.Request(
                f"{MEMORY_API_URL}/memory/load?{params}",
                headers=headers,
                method="GET",
            )
            with _urllib_request.urlopen(req, timeout=TIMEOUT) as r:
                data = json.loads(r.read())

    except Exception as e:
        return _verify_from_local(str(e))

    return _verify_data(data)


def _verify_data(data: dict) -> dict:
    content: Optional[str] = data.get("content")
    stored_checksum: Optional[str] = data.get("checksum")

    if content is None:
        return {"ok": False, "reason": "memory_md 키 없음 — save_memory_md 먼저 실행 필요"}

    if stored_checksum is None:
        # 체크섬 없는 구버전 데이터 — 경고만 하고 내용은 반환
        return {
            "ok": False,
            "reason": "checksum 키 없음 — 구버전 저장 데이터. save_memory_md로 재저장 필요",
            "content": content,
        }

    computed = compute_checksum(content)

    if computed != stored_checksum:
        return {
            "ok": False,
            "reason": "⚠️ 무결성 위반: checksum 불일치. 변조 또는 손상 의심.",
            "stored_checksum": stored_checksum,
            "computed_checksum": computed,
        }

    return {"ok": True, "content": content, "checksum": computed}


def _local_backup(data: dict) -> None:
    try:
        with open(LOCAL_FALLBACK, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _verify_from_local(api_error: str) -> dict:
    try:
        if os.path.exists(LOCAL_FALLBACK):
            with open(LOCAL_FALLBACK, encoding="utf-8") as f:
                data = json.load(f)
            result = _verify_data(data)
            result["source"] = "local_fallback"
            result["api_error"] = api_error
            return result
    except Exception:
        pass
    return {"ok": False, "reason": f"API 오류 + 로컬 폴백 없음: {api_error}"}


if __name__ == "__main__":
    import sys

    api_key = os.environ.get("MEMORY_API_KEY", "")
    if not api_key:
        print("MEMORY_API_KEY 환경변수 필요")
        sys.exit(1)

    if len(sys.argv) > 1 and sys.argv[1] == "save":
        memory_path = sys.argv[2] if len(sys.argv) > 2 else "agents/hermes/MEMORY.md"
        with open(memory_path, encoding="utf-8") as f:
            content = f.read()
        result = save_memory_md(content, api_key)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        result = load_and_verify_memory_md(api_key)
        print(json.dumps({k: v for k, v in result.items() if k != "content"}, ensure_ascii=False, indent=2))
        if result.get("ok"):
            print("[OK] MEMORY.md 무결성 검증 통과")
        else:
            print(f"[FAIL] {result.get('reason', '알 수 없는 오류')}")
