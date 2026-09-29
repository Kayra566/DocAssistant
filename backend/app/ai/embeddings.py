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
        # Kriptografik amaç yok: yalnızca kelimeyi deterministik bir kovaya eşler.
        h = int(
            hashlib.md5(tok.encode("utf-8"), usedforsecurity=False).hexdigest(), 16
        )
        idx = h % dim
        sign = 1.0 if (h // dim) % 2 == 0 else -1.0
        vec[idx] += sign
    norm = math.sqrt(sum(v * v for v in vec))
    if norm > 0:
        vec = [v / norm for v in vec]
    return vec


class Embedder:
    def __init__(self):
        self.provider = settings.EMBEDDING_PROVIDER
        self.dim = settings.EMBEDDING_DIM
        self._model = None

        if self.provider == "sentence_transformers":
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer("all-MiniLM-L6-v2")
            self.dim = self._model.get_sentence_embedding_dimension()
        elif self.provider == "ollama":
            # Boyut ilk çağrıda modelden öğrenilir.
            self.dim = 0

    async def _embed_ollama(self, texts: list[str]) -> list[list[float]]:
        import httpx

        async with httpx.AsyncClient(timeout=settings.LLM_TIMEOUT_SECONDS) as client:
            response = await client.post(
                f"{settings.OLLAMA_BASE_URL}/api/embed",
                json={"model": settings.OLLAMA_EMBED_MODEL, "input": texts},
            )
            response.raise_for_status()
            vectors = response.json().get("embeddings") or []

        if not vectors:
            raise RuntimeError(
                f"Ollama '{settings.OLLAMA_EMBED_MODEL}' modelinden embedding alınamadı."
            )
        self.dim = len(vectors[0])
        return [[float(v) for v in vec] for vec in vectors]

    async def embed(self, text: str) -> list[float]:
        return (await self.embed_many([text]))[0]

    async def embed_many(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        if self.provider == "ollama":
            return await self._embed_ollama(texts)
        if self._model is not None:
            return [
                self._model.encode(t, normalize_embeddings=True).tolist() for t in texts
            ]
        return [_hashing_embed(t, self.dim) for t in texts]


_embedder: Embedder | None = None


def get_embedder() -> Embedder:
    global _embedder
    if _embedder is None:
        _embedder = Embedder()
    return _embedder


def reset_embedder() -> None:
    global _embedder
    _embedder = None
