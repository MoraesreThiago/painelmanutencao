from __future__ import annotations

from uuid import UUID

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class UserArea(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "user_areas"
    __table_args__ = (UniqueConstraint("user_id", "area_id", name="uq_user_area_user_area"),)

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    area_id: Mapped[UUID] = mapped_column(ForeignKey("areas.id", ondelete="CASCADE"), nullable=False, index=True)

    user = relationship("User", back_populates="area_assignments")
    area = relationship("Area", back_populates="user_area_assignments")
