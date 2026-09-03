class AppError(Exception):
    """Uygulama seviyesinde temel hata."""

    status_code: int = 400
    message: str = "Bir hata oluştu."
    # i18n katalog anahtarı; özel mesaj verilmediğinde çeviri için kullanılır.
    code: str = "error.generic"

    def __init__(self, message: str | None = None, *, code: str | None = None):
        from app.core.i18n import translate

        if code:
            self.code = code
        self.custom_message = message is not None
        self.message = message or translate(self.code, "tr")
        super().__init__(self.message)


class AuthError(AppError):
    status_code = 401
    message = "Kimlik doğrulama başarısız."
    code = "error.auth"


class PermissionError(AppError):
    status_code = 403
    message = "Bu işlem için yetkiniz yok."
    code = "error.permission"


class NotFoundError(AppError):
    status_code = 404
    message = "Kayıt bulunamadı."
    code = "error.not_found"


class ConflictError(AppError):
    status_code = 409
    message = "Kayıt zaten mevcut."
    code = "error.conflict"


class ValidationError(AppError):
    status_code = 422
    message = "Geçersiz veri."
    code = "error.validation"


class LockedError(AppError):
    status_code = 423
    message = "Hesap geçici olarak kilitli."
    code = "error.locked"


class RateLimitError(AppError):
    status_code = 429
    message = "Çok fazla istek gönderildi. Lütfen bekleyin."
    code = "error.rate_limited"
