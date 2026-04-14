from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    full_name: Mapped[str] = mapped_column(String(160), nullable=False)
    email: Mapped[str] = mapped_column(String(160), unique=True, nullable=False, index=True)
    registration_number: Mapped[str | None] = mapped_column(
        String(50),
        unique=True,
        nullable=True,
    )
    job_title: Mapped[str | None] = mapped_column(String(120), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    area_id: Mapped[UUID | None] = mapped_column(ForeignKey("areas.id"), nullable=True, index=True)
    role_id: Mapped[UUID] = mapped_column(ForeignKey("roles.id"), nullable=False, index=True)

    area = relationship("Area", back_populates="users")
    area_assignments = relationship("UserArea", back_populates="user", cascade="all, delete-orphan")
    allowed_areas = relationship("Area", secondary="user_areas", viewonly=True)
    role = relationship("Role", back_populates="users")
    collaborator = relationship("Collaborator", back_populates="linked_user", uselist=False)
    movements = relationship("Movement", back_populates="moved_by_user")
    authorized_service_orders = relationship(
        "ExternalServiceOrder",
        foreign_keys="ExternalServiceOrder.authorized_by_user_id",
        back_populates="authorized_by_user",
    )
    registered_service_orders = relationship(
        "ExternalServiceOrder",
        foreign_keys="ExternalServiceOrder.registered_by_user_id",
        back_populates="registered_by_user",
    )
    motor_replacements = relationship("MotorReplacement", back_populates="registered_by_user")
    burned_motor_records = relationship("BurnedMotorRecord", back_populates="recorded_by_user")
    instrument_replacements = relationship("InstrumentReplacement", back_populates="registered_by_user")
    instrument_service_requests = relationship(
        "InstrumentServiceRequest",
        back_populates="registered_by_user",
    )
    audit_logs = relationship("AuditLog", back_populates="actor_user")

    @property
    def area_ids(self) -> list[UUID]:
        assigned_ids = [assignment.area_id for assignment in self.area_assignments]
        if assigned_ids:
            return assigned_ids
        if self.area_id is not None:
            return [self.area_id]
        return []

    @property
    def permissions(self) -> list[str]:
        from app.core.permissions import get_user_permissions

        return sorted(permission.value for permission in get_user_permissions(self))

