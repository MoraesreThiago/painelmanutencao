from __future__ import annotations

from uuid import UUID

from sqlalchemy import Enum as SqlEnum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import RecordStatus
from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Collaborator(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "collaborators"

    full_name: Mapped[str] = mapped_column(String(160), nullable=False)
    registration_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    job_title: Mapped[str | None] = mapped_column(String(120), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    status: Mapped[RecordStatus] = mapped_column(
        SqlEnum(RecordStatus, name="record_status_enum"),
        default=RecordStatus.ACTIVE,
        nullable=False,
    )
    area_id: Mapped[UUID] = mapped_column(ForeignKey("areas.id"), nullable=False, index=True)
    linked_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id"),
        unique=True,
        nullable=True,
    )

    area = relationship("Area", back_populates="collaborators")
    linked_user = relationship("User", back_populates="collaborator")

