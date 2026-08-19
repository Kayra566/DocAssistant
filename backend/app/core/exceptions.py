class AppError(Exception):
    """Uygulama seviyesinde temel hata."""

    status_code: int = 400
    message: str = "Bir hata oluştu."

    def __init__(self, message: str | None = None):
        if message:
            self.message = message
        super().__init__(self.message)


class AuthError(AppError):
    status_code = 401
    message = "Kimlik doğrulama başarısız."


class PermissionError(AppError):
    status_code = 403
    message = "Bu işlem için yetkiniz yok."


class NotFoundError(AppError):
    status_code = 404
    message = "Kayıt bulunamadı."


class ConflictError(AppError):
    status_code = 409
    message = "Kayıt zaten mevcut."


class ValidationError(AppError):
    status_code = 422
    message = "Geçersiz veri."


class LockedError(AppError):
    status_code = 423
    message = "Hesap geçici olarak kilitli."
