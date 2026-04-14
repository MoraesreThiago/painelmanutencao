from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class InstrumentReplacement(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "instrument_replacements"
    __table_args__ = (
        CheckConstraint(
            "removed_instrument_id <> installed_instrument_id",
            name="ck_instrument_replacements_distinct",
        ),
    )

    area_id: Mapped[UUID] = mapped_column(ForeignKey("areas.id"), nullable=False, index=True)
    removed_instrument_id: Mapped[UUID] = mapped_column(
        ForeignKey("instruments.equipment_id"),
        nullable=False,
        index=True,
    )
    installed_instrument_id: Mapped[UUID] = mapped_column(
        ForeignKey("instruments.equipment_id"),
        nullable=False,
        index=True,
    )
    target_equipment_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("equipments.id"),
        nullable=True,
        index=True,
    )
    target_equipment_tag: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    replaced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
        index=True,
    )
    registered_by_user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    area = relationship("Area", back_populates="instrument_replacements")
    removed_instrument = relationship(
        "Instrument",
        foreign_keys=[removed_instrument_id],
        back_populates="removal_replacements",
    )
    installed_instrument = relationship(
        "Instrument",
        foreign_keys=[installed_instrument_id],
        back_populates="installation_replacements",
    )
    target_equipment = relationship("Equipment", back_populates="instrument_replacements")
    registered_by_user = relationship("User", back_populates="instrument_replacements")
    service_requests = relationship(
        "InstrumentServiceRequest",
        back_populates="instrument_replacement",
        cascade="all, delete-orphan",
        order_by="desc(InstrumentServiceRequest.requested_at)",
    )
