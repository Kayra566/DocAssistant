"""AIJob sonucunu formatlardan bağımsız bir ara temsile çevirir.

Her renderer (pdf/docx/xlsx/md) yalnızca bu temsili tüketir; böylece yeni bir
görev tipi eklendiğinde tek bir yerde eşleme yapmak yeterli olur.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.models.ai import AIJob, AIJobType

JOB_TITLES: dict[str, str] = {
    AIJobType.CHAT: "Sohbet Yanıtı",
    AIJobType.SUMMARY: "Özet",
    AIJobType.KEYPOINTS: "Kritik Bilgiler",
    AIJobType.QUIZ: "Quiz",
    AIJobType.TRANSLATE: "Çeviri",
    AIJobType.EXTRACT: "Çıkarılan Veri",
    AIJobType.COMPARE: "Doküman Karşılaştırma",
}

QUIZ_TYPE_LABELS: dict[str, str] = {
    "multiple_choice": "Çoktan seçmeli",
    "true_false": "Doğru/Yanlış",
    "open_ended": "Açık uçlu",
}


@dataclass
class Table:
    columns: list[str]
    rows: list[list[str]]


@dataclass
class Section:
    heading: str = ""
    paragraphs: list[str] = field(default_factory=list)
    bullets: list[str] = field(default_factory=list)
    table: Table | None = None


@dataclass
class ExportDocument:
    title: str
    subtitle: str
    sections: list[Section]


def _as_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(v) for v in value if str(v).strip()]


def _paragraphs(text: str) -> list[str]:
    return [block.strip() for block in str(text).split("\n\n") if block.strip()]


def _bullet_section(heading: str, value: Any) -> Section:
    items = _as_list(value)
    return Section(heading=heading, bullets=items or ["—"])


def _quiz_sections(result: dict[str, Any]) -> list[Section]:
    questions = result.get("questions")
    if not isinstance(questions, list) or not questions:
        return [Section(heading="Sorular", paragraphs=["Soru üretilemedi."])]

    columns = ["#", "Tip", "Soru", "Seçenekler", "Cevap"]
    rows: list[list[str]] = []
    sections: list[Section] = []
    for index, raw in enumerate(questions, start=1):
        item = raw if isinstance(raw, dict) else {}
        qtype = str(item.get("type", ""))
        question = str(item.get("question", ""))
        options = _as_list(item.get("options"))
        answer = str(item.get("answer", ""))
        rows.append(
            [
                str(index),
                QUIZ_TYPE_LABELS.get(qtype, qtype),
                question,
                " | ".join(options),
                answer,
            ]
        )
        bullets = [f"{chr(64 + i)}) {opt}" for i, opt in enumerate(options, start=1)]
        sections.append(
            Section(
                heading=f"{index}. {question}",
                paragraphs=[f"Cevap: {answer}"] if answer else [],
                bullets=bullets,
            )
        )
    # Tablo ilk bölümde durur; XLSX renderer yalnızca tabloları kullanır.
    return [Section(heading="Sorular", table=Table(columns=columns, rows=rows))] + sections


def _extract_sections(result: dict[str, Any]) -> list[Section]:
    records = result.get("records")
    records = records if isinstance(records, list) else []
    columns = _as_list(result.get("columns"))
    if not columns:
        seen: list[str] = []
        for row in records:
            if isinstance(row, dict):
                seen.extend(k for k in row if k not in seen)
        columns = seen
    if not columns:
        return [Section(heading="Kayıtlar", paragraphs=["Kayıt bulunamadı."])]

    rows = [
        [str((row or {}).get(col, "")) for col in columns]
        for row in records
        if isinstance(row, dict)
    ]
    return [Section(heading="Kayıtlar", table=Table(columns=columns, rows=rows))]


def _compare_sections(result: dict[str, Any]) -> list[Section]:
    sections = [Section(heading="Özet", paragraphs=_paragraphs(result.get("summary", "")))]
    sections.append(_bullet_section("Yalnızca A'da", result.get("only_in_a")))
    sections.append(_bullet_section("Yalnızca B'de", result.get("only_in_b")))
    sections.append(_bullet_section("Değişenler", result.get("changed")))
    return sections


def _keypoints_sections(result: dict[str, Any]) -> list[Section]:
    return [
        _bullet_section("Tarihler", result.get("dates")),
        _bullet_section("İsimler", result.get("names")),
        _bullet_section("Sayılar", result.get("numbers")),
        _bullet_section("Kararlar", result.get("decisions")),
    ]


def build_export_document(job: AIJob, document_name: str) -> ExportDocument:
    result = job.result if isinstance(job.result, dict) else {}
    title = JOB_TITLES.get(str(job.type), str(job.type).title())
    created = job.created_at.strftime("%d.%m.%Y %H:%M") if job.created_at else ""
    subtitle = f"{document_name} · {created}".strip(" ·")

    if job.type == AIJobType.KEYPOINTS:
        sections = _keypoints_sections(result)
    elif job.type == AIJobType.QUIZ:
        sections = _quiz_sections(result)
    elif job.type == AIJobType.EXTRACT:
        sections = _extract_sections(result)
    elif job.type == AIJobType.COMPARE:
        sections = _compare_sections(result)
    else:
        body = _paragraphs(result.get("text", ""))
        sections = [Section(paragraphs=body or ["Sonuç boş."])]

    return ExportDocument(title=title, subtitle=subtitle, sections=sections)
