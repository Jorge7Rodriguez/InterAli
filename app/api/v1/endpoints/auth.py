from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.auth import AuthResponse, CurrentUserResponse, LoginRequest, RegisterRequest
from app.schemas.user import UserPublic
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AuthResponse:
    service = AuthService(db)
    return await service.register(payload)


@router.post("/login", response_model=AuthResponse)
async def login(
    payload: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AuthResponse:
    service = AuthService(db)
    return await service.login(payload)


@router.get("/me", response_model=CurrentUserResponse)
async def read_me(current_user: Annotated[User, Depends(get_current_user)]) -> CurrentUserResponse:
    return CurrentUserResponse.model_validate(current_user)


@router.get("/volunteers", response_model=list[UserPublic])
async def list_volunteers(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[UserPublic]:
    if current_user.role not in {UserRole.donor, UserRole.admin}:
        return []

    service = AuthService(db)
    volunteers = await service.repository.list_by_role(UserRole.volunteer)
    return [UserPublic.model_validate(volunteer) for volunteer in volunteers if volunteer.is_active]