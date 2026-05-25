from __future__ import annotations

import unittest
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException

from app.models.claim import Claim, ClaimStatus
from app.models.food_listing import FoodListing, FoodListingStatus
from app.models.user import User, UserRole
from app.schemas.food_listing import FoodListingCreate
from app.services.claim_service import ClaimService
from app.services.food_listing_service import FoodListingService


class DummySession:
    async def commit(self) -> None:
        return None


class InMemoryFoodListingRepository:
    def __init__(self) -> None:
        self.listings: dict[uuid.UUID, FoodListing] = {}

    async def create(self, listing: FoodListing) -> FoodListing:
        if listing.id is None:
            listing.id = uuid.uuid4()
        if listing.created_at is None:
            listing.created_at = datetime.now(timezone.utc)
        self.listings[listing.id] = listing
        return listing

    async def get_by_id(self, listing_id: uuid.UUID) -> FoodListing | None:
        return self.listings.get(listing_id)

    async def update(self, listing: FoodListing) -> FoodListing:
        self.listings[listing.id] = listing
        return listing

    async def delete(self, listing: FoodListing) -> None:
        self.listings.pop(listing.id, None)


class InMemoryClaimRepository:
    def __init__(self) -> None:
        self.claims: dict[uuid.UUID, Claim] = {}

    async def create(self, claim: Claim) -> Claim:
        if claim.id is None:
            claim.id = uuid.uuid4()
        now = datetime.now(timezone.utc)
        if claim.created_at is None:
            claim.created_at = now
        claim.updated_at = now
        self.claims[claim.id] = claim
        return claim

    async def get_by_id(self, claim_id: uuid.UUID) -> Claim | None:
        return self.claims.get(claim_id)

    async def get_by_listing_id(
        self,
        listing_id: uuid.UUID,
        statuses: set[str] | set[ClaimStatus] | None = None,
    ) -> Claim | None:
        for claim in self.claims.values():
            if claim.food_listing_id == listing_id:
                if statuses is not None:
                    normalized_statuses = {
                        status.value if hasattr(status, "value") else status for status in statuses
                    }
                    if claim.status.value not in normalized_statuses:
                        continue
                return claim
        return None

    async def update(self, claim: Claim) -> Claim:
        claim.updated_at = datetime.now(timezone.utc)
        self.claims[claim.id] = claim
        return claim

    async def count_active_by_volunteer(self, volunteer_id: uuid.UUID) -> int:
        return sum(
            1
            for claim in self.claims.values()
            if claim.volunteer_id == volunteer_id and claim.status in {ClaimStatus.approved, ClaimStatus.picked_up}
        )


class InMemoryUserRepository:
    def __init__(self) -> None:
        self.users: dict[uuid.UUID, User] = {}

    def add(self, user: User) -> None:
        self.users[user.id] = user

    async def list_by_role(self, role: UserRole) -> list[User]:
        return [user for user in self.users.values() if user.role == role and user.is_active]


def make_user(role: UserRole, email: str) -> User:
    now = datetime.now(timezone.utc)
    return User(
        id=uuid.uuid4(),
        email=email,
        full_name="Test User",
        hashed_password="hashed-password",
        role=role,
        is_active=True,
        created_at=now,
        updated_at=now,
    )


class ClaimFlowTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.session = DummySession()
        self.listing_repo = InMemoryFoodListingRepository()
        self.claim_repo = InMemoryClaimRepository()
        self.user_repo = InMemoryUserRepository()

        self.food_listing_service = FoodListingService(self.session)
        self.food_listing_service.repo = self.listing_repo
        self.food_listing_service.claim_repo = self.claim_repo

        self.claim_service = ClaimService(
            self.session,
            claim_repo=self.claim_repo,
            listing_repo=self.listing_repo,
            user_repo=self.user_repo,
        )

        self.donor = make_user(UserRole.donor, "donor1@example.com")
        self.second_donor = make_user(UserRole.donor, "donor2@example.com")
        self.receiver_one = make_user(UserRole.receiver, "receiver1@example.com")
        self.receiver_two = make_user(UserRole.receiver, "receiver2@example.com")

        for user in [self.donor, self.second_donor, self.receiver_one, self.receiver_two]:
            self.user_repo.add(user)

    async def test_donor_rejects_and_listing_can_be_reclaimed_by_another_receiver(self) -> None:
        listing = await self.food_listing_service.create(
            FoodListingCreate(
                title="Pan casero",
                description="Lote listo para retirar",
                quantity=3,
                category="panadería",
                pickup_address="Calle 123",
            ),
            self.donor,
        )

        first_claim = await self.claim_service.create_claim(listing.id, self.receiver_one)
        self.assertEqual(first_claim.status, ClaimStatus.pending)
        self.assertEqual(first_claim.food_listing_id, listing.id)

        rejected_claim = await self.claim_service.update_status(first_claim.id, ClaimStatus.rejected, self.donor)
        self.assertEqual(rejected_claim.status, ClaimStatus.rejected)
        self.assertEqual(rejected_claim.food_listing.status, FoodListingStatus.active)

        second_claim = await self.claim_service.create_claim(listing.id, self.receiver_two)
        self.assertEqual(second_claim.status, ClaimStatus.pending)
        self.assertEqual(second_claim.receiver_id, self.receiver_two.id)
        self.assertEqual(second_claim.food_listing.status, FoodListingStatus.claimed)
        self.assertNotEqual(second_claim.id, first_claim.id)
        self.assertEqual(self.claim_repo.claims[first_claim.id].status, ClaimStatus.rejected)

        with self.assertRaises(HTTPException) as context:
            await self.claim_service.create_claim(listing.id, self.second_donor)

        self.assertEqual(context.exception.status_code, 403)
        self.assertEqual(context.exception.detail, "Solo receivers pueden reclamar listings")

    async def test_listing_cannot_be_deleted_while_it_has_claims(self) -> None:
        listing = await self.food_listing_service.create(
            FoodListingCreate(
                title="Verduras",
                description="Caja de verduras",
                quantity=2,
                category="hortalizas",
                pickup_address="Calle 456",
            ),
            self.donor,
        )

        await self.claim_service.create_claim(listing.id, self.receiver_one)

        with self.assertRaises(HTTPException) as context:
            await self.food_listing_service.delete(listing.id, self.donor)

        self.assertEqual(context.exception.status_code, 409)
        self.assertEqual(context.exception.detail, "No se puede eliminar un listing con claims asociados")

    async def test_volunteer_can_confirm_pickup_and_delivery_after_assignment(self) -> None:
        volunteer = make_user(UserRole.volunteer, "volunteer@example.com")
        self.user_repo.add(volunteer)

        listing = await self.food_listing_service.create(
            FoodListingCreate(
                title="Arroz",
                description="Lote listo para retiro",
                quantity=5,
                category="granos",
                pickup_address="Cra 10",
            ),
            self.donor,
        )

        claim = await self.claim_service.create_claim(listing.id, self.receiver_one)
        assigned_claim = await self.claim_service.update_status(claim.id, ClaimStatus.approved, self.donor, volunteer_id=volunteer.id)

        self.assertEqual(assigned_claim.status, ClaimStatus.approved)
        self.assertEqual(assigned_claim.volunteer_id, volunteer.id)

        accepted_claim = await self.claim_service.update_status(claim.id, ClaimStatus.approved, volunteer)
        self.assertEqual(accepted_claim.status, ClaimStatus.approved)
        self.assertIsNotNone(accepted_claim.volunteer_accepted_at)

        picked_up_claim = await self.claim_service.update_status(claim.id, ClaimStatus.picked_up, volunteer)
        self.assertEqual(picked_up_claim.status, ClaimStatus.picked_up)
        self.assertIsNotNone(picked_up_claim.pickup_confirmed_at)

        delivered_claim = await self.claim_service.update_status(claim.id, ClaimStatus.delivered, volunteer)
        self.assertEqual(delivered_claim.status, ClaimStatus.delivered)
        self.assertIsNotNone(delivered_claim.delivered_confirmed_at)

    async def test_rejected_volunteer_assignment_is_reassigned_to_another_volunteer(self) -> None:
        volunteer_one = make_user(UserRole.volunteer, "volunteer1@example.com")
        volunteer_two = make_user(UserRole.volunteer, "volunteer2@example.com")
        self.user_repo.add(volunteer_one)
        self.user_repo.add(volunteer_two)

        listing = await self.food_listing_service.create(
            FoodListingCreate(
                title="Frutas",
                description="Lote listo para recoger",
                quantity=4,
                category="frutas",
                pickup_address="Cra 20",
            ),
            self.donor,
        )

        claim = await self.claim_service.create_claim(listing.id, self.receiver_one)
        assigned_claim = await self.claim_service.update_status(claim.id, ClaimStatus.approved, self.donor)

        original_volunteer_id = assigned_claim.volunteer_id
        self.assertIn(original_volunteer_id, {volunteer_one.id, volunteer_two.id})

        rejecting_volunteer = volunteer_one if original_volunteer_id == volunteer_one.id else volunteer_two
        rejected_by_first = await self.claim_service.update_status(claim.id, ClaimStatus.cancelled, rejecting_volunteer)
        self.assertEqual(rejected_by_first.status, ClaimStatus.approved)
        self.assertNotEqual(rejected_by_first.volunteer_id, original_volunteer_id)
        self.assertIsNone(rejected_by_first.volunteer_accepted_at)


if __name__ == "__main__":
    unittest.main()