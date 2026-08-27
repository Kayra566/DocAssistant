from __future__ import annotations

import json
import re
from typing import Any

_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)


def _candidates(text: str):
    fenced = _FENCE_RE.search(text)
    if fenced:
        yield fenced.group(1)
    yield text
    for opener, closer in (("{", "}"), ("[", "]")):
        start = text.find(opener)
        end = text.rfind(closer)
        if start != -1 and end > start:
            yield text[start : end + 1]


def parse_json(text: str) -> Any | None:
    """LLM çıktısından JSON ayrıştırır; başarısızsa None döner."""
    for candidate in _candidates(text or ""):
        try:
            return json.loads(candidate.strip())
        except (ValueError, TypeError):
            continue
    return None


def parse_json_object(text: str, *, keys: dict[str, Any]) -> dict[str, Any]:
    """JSON nesnesi bekler; eksik/bozuk çıktıda verilen varsayılanlara düşer.

    `keys` her beklenen anahtar için varsayılan değeri taşır.
    """
    parsed = parse_json(text)
    result: dict[str, Any] = {}
    if isinstance(parsed, dict):
        for key, default in keys.items():
            value = parsed.get(key, default)
            result[key] = default if value is None else value
    else:
        result = dict(keys)
        result["raw"] = text
    return result
