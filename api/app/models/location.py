from __future__ import annotations

from uuid import UUID

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Location(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "locations"
    __table_args__ = (
        UniqueConstraint("name", "sector", "area_id", name="uq_location_name_sector_area"),
    )

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    sector: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    area_id: Mapped[UUID] = mapped_column(ForeignKey("areas.id"), nullable=False, index=True)

    area = relationship("Area", back_populates="locations")
    equipments = relationship("Equipment", back_populates="location")
    previous_movements = relationship(
        "Movement",
        foreign_keys="Movement.previous_location_id",
        back_populates="previous_location",
    )
    new_movements = relationship(
        "Movement",
        foreign_keys="Movement.new_location_id",
        back_populates="new_location",
    )
