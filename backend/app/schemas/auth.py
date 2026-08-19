import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import Plan, Role


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)
    organization_name: str | None = Field(default=None, max_length=255)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)
    totp_code: str | None = Field(default=None, min_length=6, max_length=6)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class VerifyEmailRequest(BaseModel):
    token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


class Enable2FAResponse(BaseModel):
    secret: str
    provisioning_uri: str


class Verify2FARequest(BaseModel):
    code: str = Field(min_length=6, max_length=6)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    full_name: str | None
    is_verified: bool
    is_superuser: bool
    totp_enabled: bool
    created_at: datetime


class MembershipResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    organization_id: uuid.UUID
    role: Role


class RegisterResponse(BaseModel):
    user: UserResponse
    organization_id: uuid.UUID
    # Local geliştirmede email yerine token'ı burada döndürüyoruz (Faz 7'de kalkacak).
    dev_verification_token: str | None = None


class MessageResponse(BaseModel):
    message: str
    dev_token: str | None = None


# Yeniden dış modüllerden erişebilmek için
__all__ = [
    "RegisterRequest",
    "LoginRequest",
    "TokenResponse",
    "RefreshRequest",
    "VerifyEmailRequest",
    "ForgotPasswordRequest",
    "ResetPasswordRequest",
    "Enable2FAResponse",
    "Verify2FARequest",
    "UserResponse",
    "MembershipResponse",
    "RegisterResponse",
    "MessageResponse",
    "Plan",
]
