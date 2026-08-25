from __future__ import annotations

import hashlib
import math
import re

from app.core.config import settings

_word_re = re.compile(r"\w+", re.UNICODE)


def _hashing_embed(text: str, dim: int) -> list[float]:
    """Deterministik, bağımlılıksız embedding (bag-of-words hashing).

    Aynı metin -> aynı vektör; örtüşen kelimeler -> yüksek kosinüs benzerliği.
    Production'da sentence-transformers ile değiştirilebilir.
    """
    vec = [0.0] * dim
    for tok in _word_re.findall(text.lower()):
        h = int(hashlib.md5(tok.encode("utf-8")).hexdigest(), 16)
        idx = h % dim
        sign = 1.0 if (h // dim) % 2 == 0 else -1.0
        vec[idx] += sign
    norm = math.sqrt(sum(v * v for v in vec))
    if norm > 0:
        vec = [v / norm for v in vec]
    return vec


class Embedder:
    def __init__(self):
        self.dim = settings.EMBEDDING_DIM
        self._model = None
        if settings.EMBEDDING_PROVIDER == "sentence_transformers":
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer("all-MiniLM-L6-v2")
            self.dim = self._model.get_sentence_embedding_dimension()

    def embed(self, text: str) -> list[float]:
        if self._model is not None:
            return self._model.encode(text, normalize_embeddings=True).tolist()
        return _hashing_embed(text, self.dim)

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        return [self.embed(t) for t in texts]


_embedder: Embedder | None = None


def get_embedder() -> Embedder:
    global _embedder
    if _embedder is None:
        _embedder = Embedder()
    return _embedder
