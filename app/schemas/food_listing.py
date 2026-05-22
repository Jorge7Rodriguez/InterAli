from __future__ import annotations

import uuid
from datetime import datetime
from typing import List

from pydantic import BaseModel, ConfigDict, Field, conint

from app.models.food_listing import FoodListingStatus


class FoodListingCreate(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    quantity: conint(ge=1) = 1
    category: str | None = Field(default=None, max_length=100)
    expiration_date: datetime | None = None
    pickup_address: str | None = Field(default=None, max_length=512)


class FoodListingUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    quantity: conint(ge=1) | None = None
    category: str | None = Field(default=None, max_length=100)
    expiration_date: datetime | None = None
    pickup_address: str | None = Field(default=None, max_length=512)
    status: FoodListingStatus | None = None


class FoodListingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    donor_id: uuid.UUID
    title: str
    description: str | None
    quantity: int
    category: str | None
    expiration_date: datetime | None
    pickup_address: str | None
    status: FoodListingStatus
    created_at: datetime


class FoodListingList(BaseModel):
    items: List[FoodListingRead]
    total: int
    limit: int
    offset: int
