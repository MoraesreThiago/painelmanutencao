from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Movement(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "movements"

    equipment_id: Mapped[UUID] = mapped_column(
        ForeignKey("equipments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    previous_location_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("locations.id"),
        nullable=True,
    )
    new_location_id: Mapped[UUID | None] = mapped_column(ForeignKey("locations.id"), nullable=True)
    moved_by_user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    moved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
        index=True,
    )
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    status_after: Mapped[str | None] = mapped_column(String(80), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    equipment = relationship("Equipment", back_populates="movements")
    previous_location = relationship(
        "Location",
        foreign_keys=[previous_location_id],
        back_populates="previous_movements",
    )
    new_location = relationship(
        "Location",
        foreign_keys=[new_location_id],
        back_populates="new_movements",
    )
    moved_by_user = relationship("User", back_populates="movements")
