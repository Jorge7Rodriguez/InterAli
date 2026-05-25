from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.claim import Claim, ClaimStatus
from app.models.food_listing import FoodListingStatus
from app.models.user import User, UserRole
from app.repositories.claim_repository import ClaimRepository
from app.repositories.food_listing_repository import FoodListingRepository
from app.schemas.claim import ClaimRead


class ClaimService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.claim_repo = ClaimRepository(session)
        self.listing_repo = FoodListingRepository(session)

    async def create_claim(self, listing_id: uuid.UUID, current_user: User) -> ClaimRead:
        if current_user.role != UserRole.receiver:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo receivers pueden reclamar listings")

        listing = await self.listing_repo.get_by_id(listing_id)
        if listing is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing no encontrado")

        if listing.status != FoodListingStatus.active.value:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El listing ya no está disponible")

        now = datetime.now(timezone.utc)
        if listing.expiration_date is not None and listing.expiration_date <= now:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se puede reclamar un listing expirado")

        existing_open_claim = await self.claim_repo.get_by_listing_id(listing_id, statuses={ClaimStatus.pending})
        if existing_open_claim is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Este listing ya fue reclamado")

        claim = Claim(
            food_listing_id=listing.id,
            receiver_id=current_user.id,
            status=ClaimStatus.pending,
        )
        created_claim = await self.claim_repo.create(claim)
        listing.status = FoodListingStatus.claimed.value
        await self.listing_repo.update(listing)
        await self.session.commit()

        created_claim.food_listing = listing
        return ClaimRead.model_validate(created_claim)

    async def list_my_claims(self, current_user: User, status_filter: ClaimStatus | None = None) -> list[ClaimRead]:
        claims = await self.claim_repo.list_by_receiver(current_user.id, status=status_filter.value if status_filter else None)
        return [ClaimRead.model_validate(claim) for claim in claims]

    async def list_donor_claims(self, current_user: User, status_filter: ClaimStatus | None = None) -> list[ClaimRead]:
        status_value = status_filter.value if status_filter else None
        if current_user.role == UserRole.donor:
            claims = await self.claim_repo.list_by_donor(current_user.id, status=status_value)
            return [ClaimRead.model_validate(claim) for claim in claims]

        if current_user.role == UserRole.admin:
            claims = await self.claim_repo.list_all(status=status_value)
            return [ClaimRead.model_validate(claim) for claim in claims]

        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo donors o admin pueden ver estos claims")

    async def update_status(self, claim_id: uuid.UUID, status_value: ClaimStatus, current_user: User) -> ClaimRead:
        claim = await self.claim_repo.get_by_id(claim_id)
        if claim is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim no encontrado")

        if claim.status != ClaimStatus.pending:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El reclamo ya fue resuelto")

        listing = claim.food_listing
        if listing is None:
            listing = await self.listing_repo.get_by_id(claim.food_listing_id)

        if listing is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing no encontrado")

        if current_user.role not in {UserRole.donor, UserRole.admin} or (
            current_user.role == UserRole.donor and listing.donor_id != current_user.id
        ):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")

        claim.status = status_value

        if status_value == ClaimStatus.approved:
            listing.status = FoodListingStatus.claimed.value
        elif status_value in {ClaimStatus.rejected, ClaimStatus.cancelled}:
            listing.status = FoodListingStatus.active.value

        updated_claim = await self.claim_repo.update(claim)
        await self.listing_repo.update(listing)
        await self.session.commit()

        updated_claim.food_listing = listing
        return ClaimRead.model_validate(updated_claim)
