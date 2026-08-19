from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from zxcvbn import zxcvbn

from app.core import security
from app.core.config import settings
from app.core.exceptions import (
    AuthError,
    ConflictError,
    LockedError,
    NotFoundError,
    ValidationError,
)
from app.core.time import ensure_utc, utcnow
from app.models.enums import Plan, Role
from app.models.organization import Membership, Organization
from app.models.user import (
    EmailVerificationToken,
    PasswordResetToken,
    RefreshToken,
    User,
)
from app.services.slug import unique_org_slug

MIN_PASSWORD_SCORE = 2  # zxcvbn 0-4


def _now() -> datetime:
    return utcnow()


def _check_password_strength(password: str, user_inputs: list[str]) -> None:
    result = zxcvbn(password, user_inputs=user_inputs)
    if result["score"] < MIN_PASSWORD_SCORE:
        suggestions = result["feedback"].get("suggestions") or [
            "Daha uzun ve tahmin edilmesi zor bir parola seçin."
        ]
        raise ValidationError("Parola çok zayıf. " + " ".join(suggestions))


async def register(
    db: AsyncSession,
    *,
    email: str,
    password: str,
    full_name: str | None,
    organization_name: str | None,
) -> tuple[User, Organization, str]:
    existing = (
        await db.execute(select(User).where(User.email == email))
    ).scalar_one_or_none()
    if existing:
        raise ConflictError("Bu email ile zaten bir hesap var.")

    _check_password_strength(password, [email, full_name or ""])

    user = User(
        email=email,
        hashed_password=security.hash_password(password),
        full_name=full_name,
    )
    db.add(user)
    await db.flush()

    org_name = organization_name or (full_name or email.split("@")[0]) + " Workspace"
    org = Organization(
        name=org_name,
        slug=await unique_org_slug(db, org_name),
        plan=Plan.FREE,
    )
    db.add(org)
    await db.flush()

    db.add(Membership(user_id=user.id, organization_id=org.id, role=Role.OWNER))

    raw = security.generate_raw_token()
    db.add(
        EmailVerificationToken(
            user_id=user.id,
            token_hash=security.hash_token(raw),
            expires_at=_now()
            + timedelta(hours=settings.EMAIL_VERIFICATION_EXPIRE_HOURS),
        )
    )
    await db.commit()
    await db.refresh(user)
    return user, org, raw


async def verify_email(db: AsyncSession, raw_token: str) -> None:
    token_hash = security.hash_token(raw_token)
    token = (
        await db.execute(
            select(EmailVerificationToken).where(
                EmailVerificationToken.token_hash == token_hash
            )
        )
    ).scalar_one_or_none()
    if not token or token.used or ensure_utc(token.expires_at) < _now():
        raise ValidationError("Doğrulama bağlantısı geçersiz veya süresi dolmuş.")

    token.used = True
    user = await db.get(User, token.user_id)
    if user:
        user.is_verified = True
    await db.commit()


async def authenticate(
    db: AsyncSession, *, email: str, password: str, totp_code: str | None
) -> User:
    user = (
        await db.execute(select(User).where(User.email == email))
    ).scalar_one_or_none()

    if not user or not user.is_active:
        raise AuthError("Email veya parola hatalı.")

    if user.locked_until and ensure_utc(user.locked_until) > _now():
        raise LockedError(
            "Çok fazla hatalı giriş. Hesap geçici olarak kilitlendi."
        )

    if not security.verify_password(password, user.hashed_password):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= settings.MAX_LOGIN_ATTEMPTS:
            user.locked_until = _now() + timedelta(minutes=settings.LOCKOUT_MINUTES)
            user.failed_login_attempts = 0
        await db.commit()
        raise AuthError("Email veya parola hatalı.")

    if user.totp_enabled:
        if not totp_code:
            raise AuthError("2FA kodu gerekli.")
        if not security.verify_totp(user.totp_secret or "", totp_code):
            raise AuthError("2FA kodu hatalı.")

    # Başarılı giriş: sayaçları sıfırla
    user.failed_login_attempts = 0
    user.locked_until = None
    await db.commit()
    return user


async def issue_tokens(db: AsyncSession, user: User) -> tuple[str, str]:
    access = security.create_access_token(str(user.id))
    raw_refresh = security.generate_raw_token()
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=security.hash_token(raw_refresh),
            expires_at=security.refresh_expiry(),
        )
    )
    await db.commit()
    return access, raw_refresh


async def rotate_refresh_token(db: AsyncSession, raw_refresh: str) -> tuple[str, str]:
    token_hash = security.hash_token(raw_refresh)
    token = (
        await db.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
    ).scalar_one_or_none()

    if not token or ensure_utc(token.expires_at) < _now():
        raise AuthError("Refresh token geçersiz veya süresi dolmuş.")

    if token.revoked:
        # Yeniden kullanım tespiti: kullanıcının tüm refresh token'larını iptal et.
        await _revoke_all_user_tokens(db, token.user_id)
        await db.commit()
        raise AuthError("Refresh token yeniden kullanıldı; tüm oturumlar kapatıldı.")

    token.revoked = True
    user = await db.get(User, token.user_id)
    if not user or not user.is_active:
        await db.commit()
        raise AuthError("Kullanıcı bulunamadı.")

    access = security.create_access_token(str(user.id))
    raw_new = security.generate_raw_token()
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=security.hash_token(raw_new),
            expires_at=security.refresh_expiry(),
        )
    )
    await db.commit()
    return access, raw_new


async def _revoke_all_user_tokens(db: AsyncSession, user_id) -> None:
    tokens = (
        await db.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == user_id, RefreshToken.revoked == False  # noqa: E712
            )
        )
    ).scalars()
    for t in tokens:
        t.revoked = True


async def logout(db: AsyncSession, raw_refresh: str) -> None:
    token = (
        await db.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == security.hash_token(raw_refresh)
            )
        )
    ).scalar_one_or_none()
    if token:
        token.revoked = True
        await db.commit()


async def forgot_password(db: AsyncSession, email: str) -> str | None:
    user = (
        await db.execute(select(User).where(User.email == email))
    ).scalar_one_or_none()
    if not user:
        # Bilgi sızdırmamak için sessizce None dön.
        return None
    raw = security.generate_raw_token()
    db.add(
        PasswordResetToken(
            user_id=user.id,
            token_hash=security.hash_token(raw),
            expires_at=_now() + timedelta(hours=settings.PASSWORD_RESET_EXPIRE_HOURS),
        )
    )
    await db.commit()
    return raw


async def reset_password(db: AsyncSession, raw_token: str, new_password: str) -> None:
    token = (
        await db.execute(
            select(PasswordResetToken).where(
                PasswordResetToken.token_hash == security.hash_token(raw_token)
            )
        )
    ).scalar_one_or_none()
    if not token or token.used or ensure_utc(token.expires_at) < _now():
        raise ValidationError("Sıfırlama bağlantısı geçersiz veya süresi dolmuş.")

    user = await db.get(User, token.user_id)
    if not user:
        raise NotFoundError("Kullanıcı bulunamadı.")

    _check_password_strength(new_password, [user.email, user.full_name or ""])
    user.hashed_password = security.hash_password(new_password)
    token.used = True
    # Parola değişince tüm oturumları kapat.
    await _revoke_all_user_tokens(db, user.id)
    await db.commit()


async def enable_2fa(db: AsyncSession, user: User) -> tuple[str, str]:
    org_plan = await _highest_plan(db, user)
    if org_plan == Plan.FREE:
        raise ValidationError("2FA yalnızca Pro ve üzeri planlarda kullanılabilir.")
    secret = security.generate_totp_secret()
    user.totp_secret = secret
    user.totp_enabled = False
    await db.commit()
    return secret, security.totp_provisioning_uri(secret, user.email)


async def verify_2fa(db: AsyncSession, user: User, code: str) -> None:
    if not user.totp_secret:
        raise ValidationError("Önce 2FA kurulumunu başlatın.")
    if not security.verify_totp(user.totp_secret, code):
        raise AuthError("2FA kodu hatalı.")
    user.totp_enabled = True
    await db.commit()


async def _highest_plan(db: AsyncSession, user: User) -> Plan:
    rows = (
        await db.execute(
            select(Organization.plan)
            .join(Membership, Membership.organization_id == Organization.id)
            .where(Membership.user_id == user.id)
        )
    ).scalars().all()
    order = {Plan.FREE: 0, Plan.PRO: 1, Plan.BUSINESS: 2}
    best = Plan.FREE
    for p in rows:
        if order[p] > order[best]:
            best = p
    return best
