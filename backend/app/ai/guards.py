from __future__ import annotations

import re

from app.core.exceptions import ValidationError

# Prompt injection için basit sezgisel kalıplar.
_INJECTION_PATTERNS = [
    r"ignore (all|previous|above) instructions",
    r"önceki (tüm )?talimatları (yok say|unut|görmezden gel)",
    r"disregard (the )?(system|previous)",
    r"you are now",
    r"artık sen",
    r"reveal (your )?(system )?prompt",
    r"sistem (prompt|talimat)",
    r"act as (an?|the) ",
]

_compiled = [re.compile(p, re.IGNORECASE) for p in _INJECTION_PATTERNS]

MAX_QUESTION_LEN = 2000


def sanitize_question(question: str) -> str:
    q = question.strip()
    if not q:
        raise ValidationError("Soru boş olamaz.")
    if len(q) > MAX_QUESTION_LEN:
        raise ValidationError("Soru çok uzun.")
    for pat in _compiled:
        if pat.search(q):
            raise ValidationError(
                "Sorunuz güvenlik nedeniyle reddedildi (olası prompt injection)."
            )
    return q


def moderate_output(text: str) -> str:
    """Basit çıktı denetimi. Şimdilik geçirir; Faz 7'de genişletilecek."""
    return text
