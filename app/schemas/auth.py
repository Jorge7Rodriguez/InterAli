from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from app.models.user import UserRole
from app.schemas.user import UserPublic, UserRead

BCRYPT_MAX_PASSWORD_BYTES = 72


class RegisterRequest(BaseModel):
    email: EmailStr
    full_name: str | None = Field(default=None, min_length=2, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    confirm_password: str = Field(min_length=8, max_length=128)
    role: UserRole = UserRole.receiver

    @field_validator("password", "confirm_password")
    @classmethod
    def password_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("La contraseña no puede estar vacía")
        if len(value.encode("utf-8")) > BCRYPT_MAX_PASSWORD_BYTES:
            raise ValueError(
                "La contraseña no puede superar 72 bytes en UTF-8 por compatibilidad con bcrypt"
            )
        return value

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> EmailStr:
        return str(value).strip().lower()


    @model_validator(mode="after")
    def validate_passwords_and_role(self) -> "RegisterRequest":
        if self.password != self.confirm_password:
            raise ValueError("Las contraseñas no coinciden")
        if self.role == UserRole.admin:
            raise ValueError("No se permite registro público con rol admin")
        return self


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> EmailStr:
        return str(value).strip().lower()

    @field_validator("password")
    @classmethod
    def validate_password_bytes(cls, value: str) -> str:
        if len(value.encode("utf-8")) > BCRYPT_MAX_PASSWORD_BYTES:
            raise ValueError(
                "La contraseña no puede superar 72 bytes en UTF-8 por compatibilidad con bcrypt"
            )
        return value


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserRead


class CurrentUserResponse(UserPublic):
    pass