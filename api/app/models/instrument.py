from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import Date, Enum as SqlEnum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import InstrumentStatus
from app.db.base import Base


class Instrument(Base):
    __tablename__ = "instruments"

    equipment_id: Mapped[UUID] = mapped_column(
        ForeignKey("equipments.id", ondelete="CASCADE"),
        primary_key=True,
    )
    unique_identifier: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    instrument_type: Mapped[str] = mapped_column(String(120), nullable=False)
    current_status: Mapped[InstrumentStatus] = mapped_column(
        SqlEnum(InstrumentStatus, name="instrument_status_enum"),
        default=InstrumentStatus.IN_STOCK,
        nullable=False,
        index=True,
    )
    calibration_due_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    equipment = relationship("Equipment", back_populates="instrument")
    removal_replacements = relationship(
        "InstrumentReplacement",
        foreign_keys="InstrumentReplacement.removed_instrument_id",
        back_populates="removed_instrument",
    )
    installation_replacements = relationship(
        "InstrumentReplacement",
        foreign_keys="InstrumentReplacement.installed_instrument_id",
        back_populates="installed_instrument",
    )
    service_requests = relationship(
        "InstrumentServiceRequest",
        back_populates="instrument",
        cascade="all, delete-orphan",
        order_by="desc(InstrumentServiceRequest.requested_at)",
    )

