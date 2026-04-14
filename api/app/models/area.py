from __future__ import annotations

from sqlalchemy import Enum as SqlEnum, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import AreaCode
from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Area(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "areas"

    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    code: Mapped[AreaCode] = mapped_column(
        SqlEnum(AreaCode, name="area_code_enum"),
        unique=True,
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    users = relationship("User", back_populates="area")
    user_area_assignments = relationship("UserArea", back_populates="area", cascade="all, delete-orphan")
    authorized_users = relationship("User", secondary="user_areas", viewonly=True)
    collaborators = relationship("Collaborator", back_populates="area")
    locations = relationship("Location", back_populates="area")
    equipments = relationship("Equipment", back_populates="area")
    motor_replacements = relationship("MotorReplacement", back_populates="area")
    burned_motor_records = relationship("BurnedMotorRecord", back_populates="area")
    instrument_replacements = relationship("InstrumentReplacement", back_populates="area")
    instrument_service_requests = relationship("InstrumentServiceRequest", back_populates="area")

