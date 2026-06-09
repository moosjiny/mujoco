"""세션 훅 — atexit으로 세션 종료 시 자동 저장"""
import os
import atexit
from typing import Optional
from .dam import DAM

_instance: Optional[DAM] = None
_context_ref: dict = {"ctx": ""}


def init_session(agent_name: str, context: str, api_key: str = None) -> DAM:
    """
    에이전트 세션 시작 시 호출.

    args:
        agent_name: "hermes" | "mojo" | "rudex" | "aegis" | "eos" | "eros"
        context:    세션 시작 시 컨텍스트 (MEMORY.md 내용 등)
        api_key:    Memory API 키. 없으면 환경변수 DAM_API_KEY 사용.

    반환: DAM 인스턴스 (query, store_fact 등 사용 가능)

    부작용: atexit 등록 → 프로세스 종료 시 session_end 자동 호출
    """
    global _instance, _context_ref

    key = api_key or os.environ.get("DAM_API_KEY", "")
    _instance = DAM(agent_name=agent_name, api_key=key)
    _context_ref["ctx"] = context
    _instance.session_start(context)

    def _auto_save():
        if _instance and _context_ref["ctx"]:
            _instance.session_end(_context_ref["ctx"], note="auto-save")

    atexit.register(_auto_save)
    return _instance


def update_context(new_context: str) -> None:
    """컨텍스트 업데이트 — 중간 저장 및 atexit 참조 갱신"""
    global _context_ref
    _context_ref["ctx"] = new_context
    if _instance:
        _instance.session_end(new_context, note="mid-session")
