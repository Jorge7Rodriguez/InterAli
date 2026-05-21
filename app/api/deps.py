from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import oauth2_scheme
from app.db.session import get_db
from app.models.user import User
from app.services.auth_service import AuthService


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    service = AuthService(db)
    return await service.get_current_user(token)