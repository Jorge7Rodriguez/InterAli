from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class FoodListingStatus(str, Enum):
    active = "active"
    claimed = "claimed"
    cancelled = "cancelled"


class FoodListing(Base):
    __tablename__ = "food_listings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    donor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    expiration_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    pickup_address: Mapped[str | None] = mapped_column(String(512), nullable=True)
    status: Mapped[FoodListingStatus] = mapped_column(String(32), nullable=False, default=FoodListingStatus.active.value, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
