"""컨텍스트 텍스트 → 고정 차원 임베딩 벡터"""
import numpy as np
import hashlib
from typing import Optional

try:
    from sentence_transformers import SentenceTransformer
    _ST_AVAILABLE = True
except ImportError:
    _ST_AVAILABLE = False


class Embedder:
    """
    에이전트 컨텍스트를 고정 차원 벡터로 변환.

    우선순위:
      1. sentence-transformers (paraphrase-multilingual-MiniLM-L12-v2, d=384)
         한국어+영어 지원, 경량 (117MB)
      2. 해시 기반 폴백 (모델 불필요, d=256, 의미 유사도 없음)

    Phase 0 결정사항:
      d=384로 확정 (multilingual-MiniLM).
      저장 용량 상한: 2^(384/2) = 2^192 패턴 (사실상 무제한).
      W 행렬 크기: n_patterns × 384 × 4 bytes.
    """

    MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
    FALLBACK_DIM = 256

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or self.MODEL_NAME
        self._model = None

        if _ST_AVAILABLE:
            print(f"[DAM/Embedder] 모델 로드: {self.model_name}")
            self._model = SentenceTransformer(self.model_name)
            self.dim: int = self._model.get_sentence_embedding_dimension()
            print(f"[DAM/Embedder] dim={self.dim}")
        else:
            print("[DAM/Embedder] sentence-transformers 없음 → 해시 폴백 (dim=256)")
            print("[DAM/Embedder] 설치: pip install sentence-transformers")
            self.dim = self.FALLBACK_DIM

    def encode(self, text: str) -> np.ndarray:
        """텍스트 → L2 정규화된 벡터"""
        if self._model is not None:
            vec = self._model.encode(text, normalize_embeddings=True)
            return vec.astype(np.float32)
        return self._hash_encode(text)

    def _hash_encode(self, text: str) -> np.ndarray:
        """결정론적 해시 기반 벡터 (의미 무관, 동일 입력=동일 출력)"""
        vec = np.zeros(self.dim, dtype=np.float32)
        words = text.lower().split()
        for i, word in enumerate(words):
            digest = int(hashlib.sha256(f"{word}_{i}".encode()).hexdigest(), 16)
            for j in range(min(16, self.dim)):
                vec[(digest + j * 37) % self.dim] += 1.0 / (i + 1)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec /= norm
        return vec
