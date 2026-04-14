from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import JSON, DateTime, Enum as SqlEnum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import ExternalServiceStatus
from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class ExternalServiceOrder(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "external_service_orders"

    motor_id: Mapped[UUID] = mapped_column(ForeignKey("motors.equipment_id"), nullable=False, index=True)
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
        index=True,
    )
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    vendor_name: Mapped[str] = mapped_column(String(160), nullable=False)
    work_order_number: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    authorized_by_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    registered_by_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    expected_return_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_return_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    service_status: Mapped[ExternalServiceStatus] = mapped_column(
        SqlEnum(ExternalServiceStatus, name="external_service_status_enum"),
        default=ExternalServiceStatus.OPEN,
        nullable=False,
        index=True,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    attachments_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    motor = relationship("Motor", back_populates="external_service_orders")
    authorized_by_user = relationship(
        "User",
        foreign_keys=[authorized_by_user_id],
        back_populates="authorized_service_orders",
    )
    registered_by_user = relationship(
        "User",
        foreign_keys=[registered_by_user_id],
        back_populates="registered_service_orders",
    )

