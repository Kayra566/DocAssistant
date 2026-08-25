from __future__ import annotations

import zipfile
from io import BytesIO

from app.core.config import settings
from app.core.exceptions import ValidationError

# Uzantı -> mantıksal tip
EXT_MAP = {
    "pdf": "pdf",
    "docx": "docx",
    "xlsx": "xlsx",
    "pptx": "pptx",
    "txt": "txt",
    "md": "md",
    "markdown": "md",
    "png": "image",
    "jpg": "image",
    "jpeg": "image",
}

MIME_MAP = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "txt": "text/plain",
    "md": "text/markdown",
    "image": "image/png",
}


def _ext(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def _ooxml_kind(data: bytes) -> str | None:
    try:
        with zipfile.ZipFile(BytesIO(data)) as zf:
            names = zf.namelist()
    except zipfile.BadZipFile:
        return None
    if any(n.startswith("word/") for n in names):
        return "docx"
    if any(n.startswith("xl/") for n in names):
        return "xlsx"
    if any(n.startswith("ppt/") for n in names):
        return "pptx"
    return None


def detect_file_type(filename: str, data: bytes) -> str:
    """Magic-bytes ile gerçek dosya tipini doğrular; uzantı ile tutarsızsa reddeder."""
    ext = _ext(filename)
    if ext not in EXT_MAP:
        raise ValidationError(f"Desteklenmeyen dosya türü: .{ext}")

    expected = EXT_MAP[ext]

    # PDF
    if data[:5] == b"%PDF-":
        detected = "pdf"
    # PNG
    elif data[:8] == b"\x89PNG\r\n\x1a\n":
        detected = "image"
    # JPEG
    elif data[:3] == b"\xff\xd8\xff":
        detected = "image"
    # OOXML (zip tabanlı)
    elif data[:4] == b"PK\x03\x04":
        kind = _ooxml_kind(data)
        if kind is None:
            raise ValidationError("Geçersiz Office dosyası.")
        detected = kind
    else:
        # Metin dosyaları (txt/md): imza yok, UTF-8 doğrula
        if expected in ("txt", "md"):
            try:
                data.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise ValidationError("Metin dosyası UTF-8 değil.") from exc
            detected = expected
        else:
            raise ValidationError("Dosya imzası tanınmadı veya bozuk.")

    if detected != expected:
        raise ValidationError(
            f"Dosya içeriği uzantıyla uyuşmuyor (.{ext} beklendi, {detected} bulundu)."
        )
    return detected


def validate_size(size_bytes: int) -> None:
    limit = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if size_bytes > limit:
        raise ValidationError(
            f"Dosya çok büyük (limit {settings.MAX_UPLOAD_SIZE_MB} MB)."
        )
    if size_bytes == 0:
        raise ValidationError("Boş dosya yüklenemez.")
