"""현대 홉필드 네트워크 (Ramsauer et al. 2020)"""
import numpy as np
from typing import Optional, List, Tuple


class ModernHopfield:
    """
    현대 홉필드 네트워크.

    핵심 수식:
      retrieve(query) = softmax(beta * M @ query) @ M  (반복 수렴)

    이것은 Transformer self-attention과 수학적으로 동치다.
      - M: 메모리 뱅크 (저장된 패턴들의 행렬)
      - query: 부분 입력 벡터 (세션 시작 시 MEMORY.md 임베딩)
      - beta: 역온도. 높을수록 단일 패턴에 집중, 낮을수록 여러 패턴 혼합

    저장 용량: 2^(d/2) 패턴 (d=384이면 사실상 무제한)
    """

    def __init__(self, dim: int, beta: float = 2.0):
        self.dim = dim
        self.beta = beta
        self._memory: Optional[np.ndarray] = None  # shape: (n_patterns, dim)
        self._labels: List[str] = []

    def store(self, pattern: np.ndarray, label: str = "") -> None:
        """패턴 저장. 헤브 학습: 새 패턴을 메모리 뱅크에 추가."""
        v = pattern.astype(np.float32).flatten()
        norm = np.linalg.norm(v)
        if norm > 1e-8:
            v /= norm
        if self._memory is None:
            self._memory = v.reshape(1, -1)
        else:
            self._memory = np.vstack([self._memory, v.reshape(1, -1)])
        self._labels.append(label)

    def retrieve(self, query: np.ndarray, n_iter: int = 10) -> np.ndarray:
        """
        부분 입력 query로 전체 패턴 복원.
        에너지 함수를 반복적으로 최소화.
        """
        if self._memory is None or len(self._memory) == 0:
            return query.astype(np.float32)

        state = query.astype(np.float32).flatten()
        norm = np.linalg.norm(state)
        if norm > 1e-8:
            state /= norm

        for _ in range(n_iter):
            scores = self.beta * (self._memory @ state)  # (n_patterns,)
            # 수치 안정 softmax
            scores -= scores.max()
            weights = np.exp(scores)
            weights /= weights.sum() + 1e-10
            new_state = self._memory.T @ weights           # (dim,)
            norm = np.linalg.norm(new_state)
            if norm > 1e-8:
                new_state /= norm
            # 수렴 체크
            if np.linalg.norm(new_state - state) < 1e-6:
                break
            state = new_state

        return state

    def top_k(self, query: np.ndarray, k: int = 5) -> List[Tuple[str, float]]:
        """쿼리와 코사인 유사도 상위 k개 패턴 반환"""
        if self._memory is None or len(self._memory) == 0:
            return []
        q = query.astype(np.float32).flatten()
        norm = np.linalg.norm(q)
        if norm > 1e-8:
            q /= norm
        scores = self._memory @ q
        k = min(k, len(scores))
        idx = np.argsort(scores)[::-1][:k]
        return [(self._labels[i], float(scores[i])) for i in idx]

    def n_patterns(self) -> int:
        return 0 if self._memory is None else len(self._memory)

    # ── 직렬화 ──────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "dim": self.dim,
            "beta": self.beta,
            "memory": self._memory.tolist() if self._memory is not None else [],
            "labels": self._labels,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ModernHopfield":
        obj = cls(dim=d["dim"], beta=d.get("beta", 2.0))
        if d.get("memory"):
            obj._memory = np.array(d["memory"], dtype=np.float32)
        obj._labels = d.get("labels", [])
        return obj
