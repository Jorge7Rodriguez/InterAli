from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.claim import Claim
from app.models.food_listing import FoodListing


class ClaimRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, claim: Claim) -> Claim:
        self.session.add(claim)
        await self.session.flush()
        await self.session.refresh(claim)
        return claim

    async def get_by_id(self, claim_id: uuid.UUID) -> Claim | None:
        stmt = select(Claim).options(selectinload(Claim.food_listing)).where(Claim.id == claim_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_listing_id(self, listing_id: uuid.UUID) -> Claim | None:
        stmt = select(Claim).options(selectinload(Claim.food_listing)).where(Claim.food_listing_id == listing_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_receiver(self, receiver_id: uuid.UUID, status: str | None = None) -> list[Claim]:
        stmt = (
            select(Claim)
            .options(selectinload(Claim.food_listing))
            .where(Claim.receiver_id == receiver_id)
            .order_by(Claim.created_at.desc())
        )
        if status is not None:
            stmt = stmt.where(Claim.status == status)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_donor(self, donor_id: uuid.UUID, status: str | None = None) -> list[Claim]:
        stmt = (
            select(Claim)
            .join(FoodListing, Claim.food_listing_id == FoodListing.id)
            .options(selectinload(Claim.food_listing))
            .where(FoodListing.donor_id == donor_id)
            .order_by(Claim.created_at.desc())
        )
        if status is not None:
            stmt = stmt.where(Claim.status == status)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_all(self, status: str | None = None) -> list[Claim]:
        stmt = select(Claim).options(selectinload(Claim.food_listing)).order_by(Claim.created_at.desc())
        if status is not None:
            stmt = stmt.where(Claim.status == status)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, claim: Claim) -> Claim:
        await self.session.flush()
        await self.session.refresh(claim)
        return claim
