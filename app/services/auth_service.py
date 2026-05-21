from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest
from app.schemas.user import UserRead


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = UserRepository(session)

    async def register(self, payload: RegisterRequest) -> AuthResponse:
        existing_user = await self.repository.get_by_email(str(payload.email))
        if existing_user is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe un usuario con ese correo electrónico",
            )

        new_user = User(
            email=str(payload.email),
            full_name=payload.full_name,
            hashed_password=get_password_hash(payload.password),
            role=payload.role,
        )
        user = await self.repository.create(new_user)
        await self.session.commit()
        access_token, expires_in = create_access_token(str(user.id), user.role.value)
        return AuthResponse(
            access_token=access_token,
            expires_in=expires_in,
            user=UserRead.model_validate(user),
        )

    async def login(self, payload: LoginRequest) -> AuthResponse:
        user = await self.repository.get_by_email(str(payload.email))
        if user is None or not verify_password(payload.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuario inactivo",
            )

        access_token, expires_in = create_access_token(str(user.id), user.role.value)
        return AuthResponse(
            access_token=access_token,
            expires_in=expires_in,
            user=UserRead.model_validate(user),
        )

    async def get_current_user(self, token: str) -> User:
        payload = self._decode_token_or_raise(token)
        subject = payload.get("sub")
        try:
            user_id = uuid.UUID(str(subject))
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido o expirado",
                headers={"WWW-Authenticate": "Bearer"},
            ) from exc

        user = await self.repository.get_by_id(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario no encontrado",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuario inactivo",
            )

        return user

    @staticmethod
    def _decode_token_or_raise(token: str) -> dict[str, str]:
        try:
            from app.core.security import decode_access_token

            return decode_access_token(token)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido o expirado",
                headers={"WWW-Authenticate": "Bearer"},
            ) from exc