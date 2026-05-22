from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.food_listing import (
    FoodListingCreate,
    FoodListingList,
    FoodListingRead,
    FoodListingUpdate,
)
from app.services.food_listing_service import FoodListingService

router = APIRouter(prefix="/food-listings", tags=["food-listings"])


@router.post("", response_model=FoodListingRead, status_code=status.HTTP_201_CREATED)
async def create_listing(
    payload: FoodListingCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> FoodListingRead:
    service = FoodListingService(db)
    return await service.create(payload, current_user)


@router.get("", response_model=FoodListingList)
async def list_listings(
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    category: str | None = Query(None),
    status: str | None = Query(None),
) -> FoodListingList:
    service = FoodListingService(db)
    return await service.list(limit=limit, offset=offset, category=category, status=status)


@router.get("/{listing_id}", response_model=FoodListingRead)
async def get_listing(listing_id: uuid.UUID, db: Annotated[AsyncSession, Depends(get_db)]) -> FoodListingRead:
    service = FoodListingService(db)
    return await service.get(listing_id)


@router.patch("/{listing_id}", response_model=FoodListingRead)
async def patch_listing(
    listing_id: uuid.UUID,
    payload: FoodListingUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> FoodListingRead:
    service = FoodListingService(db)
    return await service.update(listing_id, payload, current_user)


@router.delete("/{listing_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_listing(
    listing_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    service = FoodListingService(db)
    await service.delete(listing_id, current_user)
