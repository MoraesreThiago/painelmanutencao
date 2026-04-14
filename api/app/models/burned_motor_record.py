from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import DateTime, Enum as SqlEnum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import BurnedMotorStatus
from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class BurnedMotorRecord(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "burned_motor_records"

    area_id: Mapped[UUID] = mapped_column(ForeignKey("areas.id"), nullable=False, index=True)
    motor_id: Mapped[UUID] = mapped_column(
        ForeignKey("motors.equipment_id"),
        nullable=False,
        index=True,
    )
    motor_replacement_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("motor_replacements.id"),
        nullable=True,
        index=True,
    )
    source_equipment_tag: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
        index=True,
    )
    diagnosis: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[BurnedMotorStatus] = mapped_column(
        SqlEnum(BurnedMotorStatus, name="burned_motor_status_enum"),
        default=BurnedMotorStatus.OPEN,
        nullable=False,
        index=True,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    recorded_by_user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

    area = relationship("Area", back_populates="burned_motor_records")
    motor = relationship("Motor", back_populates="burned_motor_records")
    motor_replacement = relationship("MotorReplacement", back_populates="burned_motor_records")
    recorded_by_user = relationship("User", back_populates="burned_motor_records")

