from __future__ import annotations

# Özet seviyeleri (M5)
SUMMARY_LEVELS: dict[str, str] = {
    "short": "En fazla 3 cümlelik kısa bir özet yaz.",
    "detailed": "Bölüm bölüm ilerleyen, ayrıntılı bir özet yaz.",
    "bullets": "Markdown madde işaretleri ('- ') kullanarak maddeli bir özet yaz.",
    "executive": (
        "Yöneticiye yönelik bir yönetici özeti yaz: durum, riskler, "
        "kararlar ve önerilen aksiyonlar."
    ),
}

# Prompt preset'leri (M9)
PROMPT_PRESETS: dict[str, str] = {
    "genel": "Nötr, sade ve anlaşılır bir dil kullan.",
    "hukuk": (
        "Hukuki terminolojiyi koru; taraflar, yükümlülükler, süreler, "
        "fesih ve yaptırım hükümlerini öne çıkar."
    ),
    "akademik": (
        "Akademik üslup kullan; amaç, yöntem, bulgular ve sonuçları ayrı ayrı belirt."
    ),
    "is": (
        "İş dünyasına uygun üslup kullan; maliyet, risk, zaman çizelgesi ve "
        "aksiyon maddelerini vurgula."
    ),
}

QUIZ_TYPES: tuple[str, ...] = ("multiple_choice", "true_false", "open_ended")


def build_task_prompt(
    *,
    task: str,
    instruction: str,
    context: str,
    preset: str = "genel",
    output_format: str = "text",
) -> str:
    """Doküman tabanlı AI görevleri için ortak prompt şablonu."""
    style = PROMPT_PRESETS.get(preset, PROMPT_PRESETS["genel"])
    fmt = (
        "Yanıtı YALNIZCA geçerli JSON olarak ver; açıklama veya kod bloğu ekleme."
        if output_format == "json"
        else "Yanıtı Markdown olarak ver."
    )
    return (
        f"GÖREV: {task}\n"
        f"ÜSLUP: {style}\n"
        f"BİÇİM: {fmt}\n"
        f"TALİMAT: {instruction}\n\n"
        f"BAĞLAM:\n{context}\n\n"
        "YANIT:"
    )


def summary_instruction(level: str) -> str:
    return SUMMARY_LEVELS.get(level, SUMMARY_LEVELS["short"])


KEYPOINTS_INSTRUCTION = (
    "Dokümandaki kritik bilgileri çıkar. Şu anahtarlara sahip bir JSON nesnesi üret: "
    '"dates" (tarihler), "names" (kişi/kurum isimleri), "numbers" (sayı ve tutarlar), '
    '"decisions" (alınan kararlar veya yükümlülükler). Her değer bir metin dizisidir.'
)


def quiz_instruction(question_count: int, types: list[str]) -> str:
    return (
        f"Toplam {question_count} soru üret. "
        f"İzin verilen tipler: {', '.join(types)}. "
        'Şu biçimde JSON döndür: {"questions": [{"type": "...", "question": "...", '
        '"options": ["..."], "answer": "...", "page": 1}]}. '
        "multiple_choice için 4 seçenek ver; true_false için options "
        '["Doğru", "Yanlış"] olsun; open_ended için options boş dizi olsun.'
    )


def translate_instruction(target_language: str, source_language: str | None) -> str:
    src = f"Kaynak dil: {source_language}. " if source_language else ""
    return (
        f"{src}Metni {target_language} diline çevir. "
        "Markdown biçimlendirmesini, başlıkları, listeleri ve sayıları koru. "
        "Yalnızca çeviriyi döndür."
    )


def extract_instruction(schema_hint: str | None) -> str:
    hint = (
        f" İstenen alanlar: {schema_hint}."
        if schema_hint
        else " Alanları dokümandaki tablo/liste başlıklarından türet."
    )
    return (
        "Dokümandaki tablo ve listeleri yapılandırılmış veriye dönüştür."
        + hint
        + ' Şu biçimde JSON döndür: {"columns": ["..."], '
        '"records": [{"alan": "değer"}]}.'
    )


COMPARE_INSTRUCTION = (
    "İki dokümanı karşılaştır. Şu anahtarlara sahip bir JSON nesnesi üret: "
    '"summary" (kısa karşılaştırma metni), "only_in_a" (yalnızca A\'da olanlar), '
    '"only_in_b" (yalnızca B\'de olanlar), "changed" (iki tarafta da olup farklılaşanlar). '
    "Dizi değerleri kısa metinlerden oluşsun."
)
