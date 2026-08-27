from __future__ import annotations

import json
import re

_SENTENCE_SPLIT = re.compile(r"[.\n;]+")
_WORD_RE = re.compile(r"[0-9A-Za-zÇĞİÖŞÜçğıöşü]+")
_DATE_RE = re.compile(r"\b\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\b")
_NUMBER_RE = re.compile(r"\b\d+(?:[.,]\d+)?\b")
_TASK_RE = re.compile(r"GÖREV:\s*(\w+)")
_QUIZ_COUNT_RE = re.compile(r"Toplam (\d+) soru")
_QUIZ_TYPES_RE = re.compile(r"İzin verilen tipler:\s*([^.\n]+)")
_TRANSLATE_TARGET_RE = re.compile(r"Metni (.+?) diline çevir")


def detect_task(prompt: str) -> str | None:
    match = _TASK_RE.search(prompt)
    return match.group(1) if match else None


def _sentences(context: str, limit: int) -> list[str]:
    out = [s.strip() for s in _SENTENCE_SPLIT.split(context) if len(s.strip()) > 12]
    return out[:limit]


def _split_compare_context(context: str) -> tuple[str, str]:
    if "DOKÜMAN B" in context:
        head, tail = context.split("DOKÜMAN B", 1)
        return head, tail
    return context, ""


def _terms(text: str) -> list[str]:
    return [w.lower() for w in _WORD_RE.findall(text) if len(w) > 4]


def _quiz(prompt: str, context: str) -> str:
    count_match = _QUIZ_COUNT_RE.search(prompt)
    count = int(count_match.group(1)) if count_match else 3
    types_match = _QUIZ_TYPES_RE.search(prompt)
    types = (
        [t.strip() for t in types_match.group(1).split(",") if t.strip()]
        if types_match
        else ["open_ended"]
    )
    sentences = _sentences(context, count) or ["Doküman içeriği"]
    questions = []
    for i in range(count):
        sentence = sentences[i % len(sentences)]
        qtype = types[i % len(types)]
        if qtype == "multiple_choice":
            options = [sentence[:60], "Belirtilmemiş", "İlgisiz", "Bilinmiyor"]
            answer = options[0]
        elif qtype == "true_false":
            options = ["Doğru", "Yanlış"]
            answer = "Doğru"
        else:
            options = []
            answer = sentence[:120]
        questions.append(
            {
                "type": qtype,
                "question": f"Dokümana göre '{sentence[:60]}' ifadesi doğru mudur?",
                "options": options,
                "answer": answer,
                "page": 1,
            }
        )
    return json.dumps({"questions": questions}, ensure_ascii=False)


def _keypoints(context: str) -> str:
    words = _WORD_RE.findall(context)
    return json.dumps(
        {
            "dates": sorted(set(_DATE_RE.findall(context)))[:10],
            "names": sorted({w for w in words if w[:1].isupper() and len(w) > 3})[:10],
            "numbers": sorted(set(_NUMBER_RE.findall(context)))[:10],
            "decisions": _sentences(context, 3),
        },
        ensure_ascii=False,
    )


def _extract(context: str) -> str:
    rows = _sentences(context, 5)
    return json.dumps(
        {
            "columns": ["index", "text"],
            "records": [{"index": i + 1, "text": s[:160]} for i, s in enumerate(rows)],
        },
        ensure_ascii=False,
    )


def _compare(context: str) -> str:
    left, right = _split_compare_context(context)
    a, b = set(_terms(left)), set(_terms(right))
    return json.dumps(
        {
            "summary": (
                f"A dokümanında {len(a - b)}, B dokümanında {len(b - a)} "
                f"özgün terim bulundu; {len(a & b)} terim ortak."
            ),
            "only_in_a": sorted(a - b)[:15],
            "only_in_b": sorted(b - a)[:15],
            "changed": sorted(a & b)[:15],
        },
        ensure_ascii=False,
    )


def _translate(prompt: str, context: str) -> str:
    match = _TRANSLATE_TARGET_RE.search(prompt)
    target = match.group(1) if match else "hedef"
    return f"[{target}] " + " ".join(context.split())[:600]


def fake_task_response(task: str, prompt: str, context: str) -> str | None:
    """Görev tipine göre deterministik sahte LLM çıktısı üretir."""
    if task == "summary":
        sentences = _sentences(context, 3)
        return "Özet: " + ". ".join(sentences) if sentences else "Özetlenecek içerik yok."
    if task == "keypoints":
        return _keypoints(context)
    if task == "quiz":
        return _quiz(prompt, context)
    if task == "translate":
        return _translate(prompt, context)
    if task == "extract":
        return _extract(context)
    if task == "compare":
        return _compare(context)
    return None
