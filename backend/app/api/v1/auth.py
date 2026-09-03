from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.core.i18n import normalize_locale, translate
from app.models.notification import NotificationType
from app.models.user import User
from app.notifications import templates
from app.notifications.email import send as send_email
from app.schemas.auth import (
    Enable2FAResponse,
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    RegisterResponse,
    ResetPasswordRequest,
    TokenResponse,
    UserResponse,
    Verify2FARequest,
    VerifyEmailRequest,
)
from app.services import auth as auth_service
from app.services import notifications as notification_service

router = APIRouter(prefix="/auth", tags=["auth"])


def _dev(token: str | None) -> str | None:
    return token if settings.EXPOSE_DEV_TOKENS else None


@router.post("/register", response_model=RegisterResponse, status_code=201)
async def register(
    payload: RegisterRequest,
    accept_language: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
):
    user, org, raw = await auth_service.register(
        db,
        email=payload.email,
        password=payload.password,
        full_name=payload.full_name,
        organization_name=payload.organization_name,
    )
    locale = normalize_locale(accept_language)
    send_email(templates.verification_email(user.email, raw, locale))
    await notification_service.create(
        db,
        user_id=user.id,
        org_id=org.id,
        type=NotificationType.WELCOME,
        title=translate("notification.welcome.title", locale),
        body=translate("notification.welcome.body", locale),
        link=f"/organizations/{org.id}/documents",
    )
    return RegisterResponse(
        user=UserResponse.model_validate(user),
        organization_id=org.id,
        dev_verification_token=_dev(raw),
    )


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(payload: VerifyEmailRequest, db: AsyncSession = Depends(get_db)):
    await auth_service.verify_email(db, payload.token)
    return MessageResponse(message="Email doğrulandı.")


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await auth_service.authenticate(
        db, email=payload.email, password=payload.password, totp_code=payload.totp_code
    )
    access, refresh = await auth_service.issue_tokens(db, user)
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    access, new_refresh = await auth_service.rotate_refresh_token(
        db, payload.refresh_token
    )
    return TokenResponse(access_token=access, refresh_token=new_refresh)


@router.post("/logout", response_model=MessageResponse)
async def logout(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    await auth_service.logout(db, payload.refresh_token)
    return MessageResponse(message="Oturum kapatıldı.")


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    payload: ForgotPasswordRequest,
    accept_language: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
):
    raw = await auth_service.forgot_password(db, payload.email)
    if raw:
        send_email(
            templates.password_reset_email(
                payload.email, raw, normalize_locale(accept_language)
            )
        )
    # Bilgi sızdırmamak için her durumda aynı mesaj.
    return MessageResponse(
        message="Eğer bu email kayıtlıysa sıfırlama bağlantısı gönderildi.",
        dev_token=_dev(raw),
    )


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    payload: ResetPasswordRequest, db: AsyncSession = Depends(get_db)
):
    await auth_service.reset_password(db, payload.token, payload.new_password)
    return MessageResponse(message="Parola güncellendi.")


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)):
    return UserResponse.model_validate(user)


@router.post("/2fa/enable", response_model=Enable2FAResponse)
async def enable_2fa(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    secret, uri = await auth_service.enable_2fa(db, user)
    return Enable2FAResponse(secret=secret, provisioning_uri=uri)


@router.post("/2fa/verify", response_model=MessageResponse)
async def verify_2fa(
    payload: Verify2FARequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await auth_service.verify_2fa(db, user, payload.code)
    return MessageResponse(message="2FA etkinleştirildi.")
