from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.claim import ClaimStatus
from app.schemas.user import UserPublic
from app.schemas.food_listing import FoodListingRead


class ClaimRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    food_listing_id: uuid.UUID
    receiver_id: uuid.UUID
    volunteer_id: uuid.UUID | None = None
    status: ClaimStatus
    volunteer_accepted_at: datetime | None = None
    pickup_confirmed_at: datetime | None = None
    delivered_confirmed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    food_listing: FoodListingRead | None = None
    receiver: UserPublic | None = None
    volunteer: UserPublic | None = None


class ClaimStatusUpdate(BaseModel):
    status: ClaimStatus
    volunteer_id: uuid.UUID | None = None

