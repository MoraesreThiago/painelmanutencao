from __future__ import annotations

from sqlalchemy import Enum as SqlEnum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import RoleName
from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Role(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "roles"

    name: Mapped[RoleName] = mapped_column(
        SqlEnum(RoleName, name="role_name_enum"),
        unique=True,
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    users = relationship("User", back_populates="role")

