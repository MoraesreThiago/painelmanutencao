from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.core.enums import BurnedMotorStatus
from app.schemas.common import IDSchema, ORMModel, TimestampSchema
from app.schemas.motor import MotorRead
from app.schemas.motor_replacement import MotorReplacementRead
from app.schemas.user import UserSummary


class BurnedMotorRecordBase(BaseModel):
    motor_id: UUID
    motor_replacement_id: UUID | None = None
    source_equipment_tag: str
    diagnosis: str
    recorded_at: datetime | None = None
    status: BurnedMotorStatus = BurnedMotorStatus.OPEN
    notes: str | None = None


class BurnedMotorRecordCreate(BurnedMotorRecordBase):
    pass


class BurnedMotorRecordUpdate(BaseModel):
    diagnosis: str | None = None
    recorded_at: datetime | None = None
    status: BurnedMotorStatus | None = None
    notes: str | None = None


class BurnedMotorRecordRead(BurnedMotorRecordBase, IDSchema, TimestampSchema, ORMModel):
    area_id: UUID
    recorded_by_user_id: UUID
    motor: MotorRead
    motor_replacement: MotorReplacementRead | None = None
    recorded_by_user: UserSummary | None = None

