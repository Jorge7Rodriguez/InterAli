from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Tuple

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.food_listing import FoodListing, FoodListingStatus
from app.models.user import UserRole, User
from app.repositories.claim_repository import ClaimRepository
from app.repositories.food_listing_repository import FoodListingRepository
from app.schemas.food_listing import (
    FoodListingCreate,
    FoodListingList,
    FoodListingRead,
    FoodListingUpdate,
)


class FoodListingService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = FoodListingRepository(session)
        self.claim_repo = ClaimRepository(session)

    async def create(self, payload: FoodListingCreate, current_user: User) -> FoodListingRead:
        if current_user is None or current_user.role != UserRole.donor:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo donors pueden crear listings")

        now = datetime.now(timezone.utc)
        listing = FoodListing(
            donor_id=current_user.id,
            title=payload.title,
            description=payload.description,
            quantity=payload.quantity,
            category=payload.category,
            expiration_date=payload.expiration_date,
            pickup_address=payload.pickup_address,
            status=FoodListingStatus.active.value,
            created_at=now,
        )

        created = await self.repo.create(listing)
        await self.session.commit()
        return FoodListingRead.model_validate(created)

    async def get(self, listing_id: uuid.UUID) -> FoodListingRead:
        listing = await self.repo.get_by_id(listing_id)
        if listing is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing no encontrado")
        return FoodListingRead.model_validate(listing)

    async def delete(self, listing_id: uuid.UUID, current_user: User) -> None:
        listing = await self.repo.get_by_id(listing_id)
        if listing is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing no encontrado")
        if listing.donor_id != current_user.id and current_user.role != UserRole.admin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")

        existing_claim = await self.claim_repo.get_by_listing_id(listing_id)
        if existing_claim is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="No se puede eliminar un listing con claims asociados",
            )

        await self.repo.delete(listing)
        await self.session.commit()

    async def update(self, listing_id: uuid.UUID, payload: FoodListingUpdate, current_user: User) -> FoodListingRead:
        listing = await self.repo.get_by_id(listing_id)
        if listing is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing no encontrado")
        if listing.donor_id != current_user.id and current_user.role != UserRole.admin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")

        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(listing, field, value)

        updated = await self.repo.update(listing)
        await self.session.commit()
        return FoodListingRead.model_validate(updated)

    async def list(
        self, limit: int = 20, offset: int = 0, category: str | None = None, status: str | None = None
    ) -> FoodListingList:
        items, total = await self.repo.list(limit=limit, offset=offset, category=category, status=status)
        return FoodListingList(items=[FoodListingRead.model_validate(i) for i in items], total=total, limit=limit, offset=offset)
