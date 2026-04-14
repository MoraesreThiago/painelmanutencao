from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Enum as SqlEnum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import EquipmentStatus, EquipmentType
from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Equipment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "equipments"

    code: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    tag: Mapped[str | None] = mapped_column(String(80), unique=True, nullable=True, index=True)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    sector: Mapped[str] = mapped_column(String(120), nullable=False)
    manufacturer: Mapped[str | None] = mapped_column(String(120), nullable=True)
    model: Mapped[str | None] = mapped_column(String(120), nullable=True)
    serial_number: Mapped[str | None] = mapped_column(String(120), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    type: Mapped[EquipmentType] = mapped_column(
        SqlEnum(EquipmentType, name="equipment_type_enum"),
        default=EquipmentType.GENERIC,
        nullable=False,
        index=True,
    )
    status: Mapped[EquipmentStatus] = mapped_column(
        SqlEnum(EquipmentStatus, name="equipment_status_enum"),
        default=EquipmentStatus.ACTIVE,
        nullable=False,
        index=True,
    )
    registered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    area_id: Mapped[UUID] = mapped_column(ForeignKey("areas.id"), nullable=False, index=True)
    location_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("locations.id"),
        nullable=True,
        index=True,
    )

    area = relationship("Area", back_populates="equipments")
    location = relationship("Location", back_populates="equipments")
    motor = relationship("Motor", back_populates="equipment", uselist=False, cascade="all, delete-orphan")
    instrument = relationship(
        "Instrument",
        back_populates="equipment",
        uselist=False,
        cascade="all, delete-orphan",
    )
    movements = relationship(
        "Movement",
        back_populates="equipment",
        cascade="all, delete-orphan",
        order_by="desc(Movement.moved_at)",
    )
    motor_replacements = relationship("MotorReplacement", back_populates="target_equipment")
    instrument_replacements = relationship("InstrumentReplacement", back_populates="target_equipment")

