from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import DateTime, Enum as SqlEnum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import InstrumentServiceStatus, InstrumentServiceType
from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class InstrumentServiceRequest(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "instrument_service_requests"

    area_id: Mapped[UUID] = mapped_column(ForeignKey("areas.id"), nullable=False, index=True)
    instrument_id: Mapped[UUID] = mapped_column(
        ForeignKey("instruments.equipment_id"),
        nullable=False,
        index=True,
    )
    instrument_replacement_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("instrument_replacements.id"),
        nullable=True,
        index=True,
    )
    service_type: Mapped[InstrumentServiceType] = mapped_column(
        SqlEnum(InstrumentServiceType, name="instrument_service_type_enum"),
        nullable=False,
        index=True,
    )
    service_status: Mapped[InstrumentServiceStatus] = mapped_column(
        SqlEnum(InstrumentServiceStatus, name="instrument_service_status_enum"),
        default=InstrumentServiceStatus.OPEN,
        nullable=False,
        index=True,
    )
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
        index=True,
    )
    expected_return_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_return_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    vendor_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    vendor_reference: Mapped[str | None] = mapped_column(String(80), nullable=True)
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    registered_by_user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

    area = relationship("Area", back_populates="instrument_service_requests")
    instrument = relationship("Instrument", back_populates="service_requests")
    instrument_replacement = relationship(
        "InstrumentReplacement",
        back_populates="service_requests",
    )
    registered_by_user = relationship("User", back_populates="instrument_service_requests")

