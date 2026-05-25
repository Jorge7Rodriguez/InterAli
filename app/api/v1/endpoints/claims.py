from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.claim import ClaimStatus
from app.models.user import User
from app.schemas.claim import ClaimRead, ClaimStatusUpdate
from app.services.claim_service import ClaimService

router = APIRouter(tags=["claims"])


@router.post("/food-listings/{listing_id}/claim", response_model=ClaimRead)
async def claim_food_listing(
    listing_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ClaimRead:
    service = ClaimService(db)
    return await service.create_claim(listing_id, current_user)


@router.get("/claims/me", response_model=list[ClaimRead])
async def list_my_claims(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    status: ClaimStatus | None = Query(default=None),
) -> list[ClaimRead]:
    service = ClaimService(db)
    return await service.list_my_claims(current_user, status_filter=status)


@router.get("/claims/donor", response_model=list[ClaimRead])
async def list_donor_claims(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    status: ClaimStatus | None = Query(default=None),
) -> list[ClaimRead]:
    service = ClaimService(db)
    return await service.list_donor_claims(current_user, status_filter=status)


@router.get("/claims/volunteer", response_model=list[ClaimRead])
async def list_volunteer_claims(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    status: ClaimStatus | None = Query(default=None),
) -> list[ClaimRead]:
    service = ClaimService(db)
    return await service.list_donor_claims(current_user, status_filter=status)


@router.patch("/claims/{claim_id}/status", response_model=ClaimRead)
async def update_claim_status(
    claim_id: uuid.UUID,
    payload: ClaimStatusUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ClaimRead:
    service = ClaimService(db)
    return await service.update_status(claim_id, payload.status, current_user, volunteer_id=payload.volunteer_id)
