from __future__ import annotations

# Basit, bağımlılıksız chunker: sayfa metnini örtüşmeli parçalara böler.
# Sayfa eşlemesi korunur (her chunk hangi sayfadan geldiğini bilir).

DEFAULT_CHUNK_SIZE = 800
DEFAULT_OVERLAP = 120


def _split_text(text: str, size: int, overlap: int) -> list[str]:
    text = text.strip()
    if not text:
        return []
    chunks: list[str] = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + size, n)
        # Kelime ortasında kesmemek için son boşluğa geri sar.
        if end < n:
            space = text.rfind(" ", start, end)
            if space > start:
                end = space
        chunks.append(text[start:end].strip())
        if end >= n:
            break
        start = max(end - overlap, start + 1)
    return [c for c in chunks if c]


def chunk_pages(
    pages: list[tuple[int, str]],
    size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP,
) -> list[tuple[int, int, str]]:
    """(chunk_index, page, content) listesi döndürür."""
    result: list[tuple[int, int, str]] = []
    idx = 0
    for page_no, text in pages:
        for piece in _split_text(text, size, overlap):
            result.append((idx, page_no, piece))
            idx += 1
    return result
