from __future__ import annotations

import uuid
from typing import List, Tuple

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.food_listing import FoodListing


class FoodListingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, listing: FoodListing) -> FoodListing:
        self.session.add(listing)
        await self.session.flush()
        await self.session.refresh(listing)
        return listing

    async def get_by_id(self, listing_id: uuid.UUID) -> FoodListing | None:
        result = await self.session.execute(select(FoodListing).where(FoodListing.id == listing_id))
        return result.scalar_one_or_none()

    async def delete(self, listing: FoodListing) -> None:
        await self.session.delete(listing)

    async def update(self, listing: FoodListing) -> FoodListing:
        await self.session.flush()
        await self.session.refresh(listing)
        return listing

    async def list(
        self,
        limit: int = 20,
        offset: int = 0,
        category: str | None = None,
        status: str | None = None,
    ) -> Tuple[List[FoodListing], int]:
        stmt = select(FoodListing)
        count_stmt = select(func.count()).select_from(FoodListing)

        if category:
            stmt = stmt.where(FoodListing.category == category)
            count_stmt = count_stmt.where(FoodListing.category == category)
        if status:
            stmt = stmt.where(FoodListing.status == status)
            count_stmt = count_stmt.where(FoodListing.status == status)

        stmt = stmt.order_by(FoodListing.created_at.desc()).limit(limit).offset(offset)

        result = await self.session.execute(stmt)
        items = result.scalars().all()

        total_res = await self.session.execute(count_stmt)
        total = total_res.scalar_one()

        return items, int(total)
