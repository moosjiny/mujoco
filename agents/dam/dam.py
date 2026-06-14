"""ROOPS-DAM 메인 인터페이스"""
from datetime import datetime
from typing import List, Tuple, Optional
import numpy as np

from .embedder import Embedder
from .hopfield import ModernHopfield
from .w_store import WStore

AGENTS = ["hermes", "mojo", "rudex", "aegis", "eos", "eros"]


class DAM:
    """
    ROOPS Distributed Associative Memory.

    에이전트가 세션 시작/종료 시 호출하여
    팀 전체 지식을 홉필드 네트워크로 공유한다.

    사용 예:
        dam = DAM("hermes", api_key="...")

        # 세션 시작: 관련 팀 기억 복원
        hits = dam.session_start("오늘 thesis 제출 및 ADR-002 검토 예정")
        for label, score in hits:
            print(f"{score:.3f} {label}")

        # 작업 중 검색
        hits = dam.query("ADR-002 홉필드 초안")

        # 세션 종료: 내 기억 저장
        dam.session_end(my_context, note="thesis v2 제출 완료")
    """

    def __init__(self, agent_name: str, api_key: str, beta: float = 2.0):
        if agent_name not in AGENTS:
            raise ValueError(f"알 수 없는 에이전트: {agent_name}. 허용: {AGENTS}")
        self.agent = agent_name
        self.embedder = Embedder()
        self.store = WStore(api_key)
        self.beta = beta
        self._net: Optional[ModernHopfield] = None

    # ── 내부 헬퍼 ────────────────────────────────────────────

    def _net_or_load(self) -> ModernHopfield:
        if self._net is None:
            loaded = self.store.load()
            self._net = loaded if loaded is not None else ModernHopfield(
                dim=self.embedder.dim, beta=self.beta
            )
            if loaded is None:
                print(f"[DAM] 새 네트워크 초기화 (dim={self.embedder.dim})")
        return self._net

    # ── 공개 API ─────────────────────────────────────────────

    def session_start(self, context: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """
        세션 시작 시 호출.
        현재 컨텍스트와 유사한 팀 기억 반환.

        반환: [(레이블, 코사인_유사도), ...] 상위 top_k개
          레이블 형식: "에이전트|YYYYMMDD_HHMM|노트"
        """
        net = self._net_or_load()
        if net.n_patterns() == 0:
            print(f"[DAM:{self.agent}] 저장된 팀 기억 없음")
            return []

        query = self.embedder.encode(context)
        hits = net.top_k(query, k=top_k)
        print(f"[DAM:{self.agent}] 세션 시작 — 관련 기억 {len(hits)}개:")
        for label, score in hits:
            print(f"  {score:+.3f}  {label}")
        return hits

    def session_end(self, context: str, note: str = "") -> bool:
        """
        세션 종료 전 호출.
        현재 컨텍스트를 팀 네트워크에 저장.
        """
        net = self._net_or_load()
        vec = self.embedder.encode(context)
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M")
        label = f"{self.agent}|{ts}|{note[:50]}"
        net.store(vec, label=label)
        ok = self.store.save(net, agent=self.agent, note=note)
        print(f"[DAM:{self.agent}] 세션 종료 — {'저장 완료' if ok else '로컬만 저장'}: {label}")
        return ok

    def query(self, question: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """
        특정 질문으로 팀 기억 검색.
        예: dam.query("ADR-002 홉필드 초안")
        """
        net = self._net_or_load()
        if net.n_patterns() == 0:
            return []
        vec = self.embedder.encode(question)
        return net.top_k(vec, k=top_k)

    def store_fact(self, text: str, note: str = "") -> None:
        """임의 텍스트를 즉시 팀 네트워크에 저장 (세션 외 사용 가능)"""
        net = self._net_or_load()
        vec = self.embedder.encode(text)
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M")
        label = f"{self.agent}|{ts}|fact:{note[:40]}"
        net.store(vec, label=label)
        self.store.save(net, agent=self.agent, note=f"fact: {note}")

    def status(self) -> dict:
        net = self._net_or_load()
        return {
            "agent": self.agent,
            "dim": self.embedder.dim,
            "n_patterns": net.n_patterns(),
            "recent": net._labels[-5:],
        }
