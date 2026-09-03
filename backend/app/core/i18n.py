"""Backend i18n: hata mesajları ve e-posta şablonları için TR/EN katalog."""

from __future__ import annotations

from typing import Literal

Locale = Literal["tr", "en"]
SUPPORTED: tuple[Locale, ...] = ("tr", "en")

CATALOG: dict[str, dict[Locale, str]] = {
    "error.generic": {
        "tr": "Bir hata oluştu.",
        "en": "Something went wrong.",
    },
    "error.auth": {
        "tr": "Kimlik doğrulama başarısız.",
        "en": "Authentication failed.",
    },
    "error.auth.missing_header": {
        "tr": "Yetkilendirme başlığı eksik.",
        "en": "Authorization header is missing.",
    },
    "error.auth.invalid_token": {
        "tr": "Token geçersiz veya süresi dolmuş.",
        "en": "Token is invalid or expired.",
    },
    "error.auth.inactive_user": {
        "tr": "Kullanıcı bulunamadı veya pasif.",
        "en": "User not found or inactive.",
    },
    "error.permission.not_member": {
        "tr": "Bu organizasyona üye değilsiniz.",
        "en": "You are not a member of this organization.",
    },
    "error.permission.superuser_required": {
        "tr": "Bu işlem için platform yöneticisi olmalısınız.",
        "en": "Platform administrator access is required.",
    },
    "error.permission": {
        "tr": "Bu işlem için yetkiniz yok.",
        "en": "You do not have permission for this action.",
    },
    "error.not_found": {
        "tr": "Kayıt bulunamadı.",
        "en": "Record not found.",
    },
    "error.conflict": {
        "tr": "Kayıt zaten mevcut.",
        "en": "Record already exists.",
    },
    "error.validation": {
        "tr": "Geçersiz veri.",
        "en": "Invalid data.",
    },
    "error.locked": {
        "tr": "Hesap geçici olarak kilitli.",
        "en": "Account is temporarily locked.",
    },
    "error.quota": {
        "tr": "Plan kotası aşıldı.",
        "en": "Plan quota exceeded.",
    },
    "error.rate_limited": {
        "tr": "Çok fazla istek gönderildi. Lütfen bekleyin.",
        "en": "Too many requests. Please wait.",
    },
    "email.verify.subject": {
        "tr": "DocAssistant hesabınızı doğrulayın",
        "en": "Verify your DocAssistant account",
    },
    "email.verify.body": {
        "tr": "Hesabınızı doğrulamak için bağlantıya tıklayın:",
        "en": "Click the link below to verify your account:",
    },
    "email.reset.subject": {
        "tr": "Parola sıfırlama talebi",
        "en": "Password reset request",
    },
    "email.reset.body": {
        "tr": "Parolanızı sıfırlamak için bağlantıya tıklayın. Bağlantı kısa sürede geçersiz olur.",
        "en": "Click the link below to reset your password. The link expires shortly.",
    },
    "email.invite.subject": {
        "tr": "Bir ekibe davet edildiniz",
        "en": "You have been invited to a team",
    },
    "email.invite.body": {
        "tr": "Daveti kabul etmek için bağlantıya tıklayın:",
        "en": "Click the link below to accept the invitation:",
    },
    "email.payment_failed.subject": {
        "tr": "Ödemeniz alınamadı",
        "en": "Your payment failed",
    },
    "email.payment_failed.body": {
        "tr": (
            "Aboneliğinizin ödemesi alınamadı. Plan kesintisi yaşamamak için ödeme "
            "yönteminizi güncelleyin."
        ),
        "en": (
            "We could not collect your subscription payment. Update your payment "
            "method to avoid interruption."
        ),
    },
    "email.quota_warning.subject": {
        "tr": "Plan kotanız dolmak üzere",
        "en": "You are close to your plan quota",
    },
    "email.quota_warning.body": {
        "tr": (
            "Aylık kullanımınız plan limitine yaklaştı. Kesintisiz devam için planınızı "
            "yükseltebilirsiniz."
        ),
        "en": (
            "Your monthly usage is close to the plan limit. Upgrade to continue "
            "without interruption."
        ),
    },
    "notification.welcome.title": {
        "tr": "DocAssistant'a hoş geldiniz",
        "en": "Welcome to DocAssistant",
    },
    "notification.welcome.body": {
        "tr": "İlk dokümanınızı yükleyerek başlayın; ardından sohbet ve AI araçlarını deneyin.",
        "en": "Start by uploading your first document, then try chat and the AI tools.",
    },
}


def normalize_locale(value: str | None) -> Locale:
    """Accept-Language başlığından desteklenen bir dil seçer."""
    if not value:
        return "tr"
    for part in value.split(","):
        code = part.split(";")[0].strip().lower()[:2]
        if code in SUPPORTED:
            return code  # type: ignore[return-value]
    return "tr"


def translate(key: str, locale: Locale = "tr", **params: object) -> str:
    entry = CATALOG.get(key)
    if not entry:
        return key
    text = entry.get(locale) or entry["tr"]
    return text.format(**params) if params else text
