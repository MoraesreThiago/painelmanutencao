from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import Date, Enum as SqlEnum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import MotorStatus
from app.db.base import Base


class Motor(Base):
    __tablename__ = "motors"

    equipment_id: Mapped[UUID] = mapped_column(
        ForeignKey("equipments.id", ondelete="CASCADE"),
        primary_key=True,
    )
    unique_identifier: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    current_status: Mapped[MotorStatus] = mapped_column(
        SqlEnum(MotorStatus, name="motor_status_enum"),
        default=MotorStatus.IN_OPERATION,
        nullable=False,
        index=True,
    )
    last_internal_service_at: Mapped[date | None] = mapped_column(Date, nullable=True)

    equipment = relationship("Equipment", back_populates="motor")
    external_service_orders = relationship(
        "ExternalServiceOrder",
        back_populates="motor",
        cascade="all, delete-orphan",
        order_by="desc(ExternalServiceOrder.sent_at)",
    )
    removal_replacements = relationship(
        "MotorReplacement",
        foreign_keys="MotorReplacement.removed_motor_id",
        back_populates="removed_motor",
    )
    installation_replacements = relationship(
        "MotorReplacement",
        foreign_keys="MotorReplacement.installed_motor_id",
        back_populates="installed_motor",
    )
    burned_motor_records = relationship(
        "BurnedMotorRecord",
        back_populates="motor",
        cascade="all, delete-orphan",
        order_by="desc(BurnedMotorRecord.recorded_at)",
    )

