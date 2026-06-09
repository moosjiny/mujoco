"""홉필드 네트워크 상태(W)를 Memory API에 영속 저장/로드"""
import json
import os
import requests
from datetime import datetime
from typing import Optional

from .hopfield import ModernHopfield

MEMORY_API_URL = "https://egs.hyperbook.com"
DAM_KEY = "roops_dam_state"
LOCAL_CACHE = os.path.expanduser("~/.roops_dam_cache.json")
TIMEOUT = 10


class WStore:
    """
    홉필드 W 행렬을 Memory API에 저장.

    저장 구조 (Memory API /memory/save payload):
      {
        "agent": "dam_system",
        "key": "roops_dam_state",
        "data": {
          "hopfield": { dim, beta, memory, labels },
          "updated_by": "hermes",
          "updated_at": "2026-06-09T...",
          "n_patterns": 12
        }
      }

    로컬 폴백: ~/.roops_dam_cache.json
    Memory API 실패 시 자동으로 로컬에만 저장.
    """

    def __init__(self, api_key: str):
        self._headers = {"x-api-key": api_key}

    def save(self, net: ModernHopfield, agent: str, note: str = "") -> bool:
        payload = {
            "agent": "dam_system",
            "key": DAM_KEY,
            "data": {
                "hopfield": net.to_dict(),
                "updated_by": agent,
                "updated_at": datetime.utcnow().isoformat(),
                "note": note,
                "n_patterns": net.n_patterns(),
            },
        }
        self._local_backup(payload["data"])  # 항상 로컬 백업 먼저
        try:
            resp = requests.post(
                f"{MEMORY_API_URL}/memory/save",
                json=payload,
                headers=self._headers,
                timeout=TIMEOUT,
            )
            if resp.status_code == 200:
                print(f"[DAM/WStore] 저장 완료: {net.n_patterns()}개 패턴 (by {agent})")
                return True
            print(f"[DAM/WStore] API 저장 실패 {resp.status_code}: {resp.text[:80]}")
        except Exception as e:
            print(f"[DAM/WStore] API 연결 오류: {e}")
        print("[DAM/WStore] 로컬 캐시에만 저장됨")
        return False

    def load(self) -> Optional[ModernHopfield]:
        try:
            resp = requests.get(
                f"{MEMORY_API_URL}/memory/load",
                params={"agent": "dam_system", "key": DAM_KEY},
                headers=self._headers,
                timeout=TIMEOUT,
            )
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, dict) and "hopfield" in data:
                    net = ModernHopfield.from_dict(data["hopfield"])
                    print(f"[DAM/WStore] API 로드: {net.n_patterns()}개 패턴")
                    return net
        except Exception as e:
            print(f"[DAM/WStore] API 로드 오류: {e}")

        return self._local_load()

    def _local_backup(self, data: dict) -> None:
        try:
            with open(LOCAL_CACHE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _local_load(self) -> Optional[ModernHopfield]:
        try:
            if os.path.exists(LOCAL_CACHE):
                with open(LOCAL_CACHE, encoding="utf-8") as f:
                    data = json.load(f)
                if "hopfield" in data:
                    net = ModernHopfield.from_dict(data["hopfield"])
                    print(f"[DAM/WStore] 로컬 캐시 로드: {net.n_patterns()}개 패턴")
                    return net
        except Exception as e:
            print(f"[DAM/WStore] 로컬 로드 오류: {e}")
        return None
