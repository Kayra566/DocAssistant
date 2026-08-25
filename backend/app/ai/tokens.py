from __future__ import annotations

import re

_word_re = re.compile(r"\S+")


def estimate_tokens(text: str) -> int:
    """Kaba token tahmini (~4 karakter/token). Gerçek tokenizer'a geçilebilir."""
    if not text:
        return 0
    return max(len(_word_re.findall(text)), len(text) // 4)
