from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.services.auth_service import AuthService


bearer_scheme = HTTPBearer()


async def get_current_user(
    creds: Annotated[HTTPAuthorizationCredentials, Security(bearer_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    token = creds.credentials
    service = AuthService(db)
    return await service.get_current_user(token)