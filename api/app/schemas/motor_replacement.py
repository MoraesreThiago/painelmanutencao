from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.schemas.common import IDSchema, ORMModel, TimestampSchema
from app.schemas.equipment import EquipmentRead
from app.schemas.motor import MotorRead
from app.schemas.user import UserSummary


class MotorReplacementBase(BaseModel):
    removed_motor_id: UUID
    installed_motor_id: UUID
    target_equipment_id: UUID | None = None
    target_equipment_tag: str
    reason: str
    replaced_at: datetime | None = None
    notes: str | None = None


class MotorReplacementCreate(MotorReplacementBase):
    pass


class MotorReplacementRead(MotorReplacementBase, IDSchema, TimestampSchema, ORMModel):
    area_id: UUID
    registered_by_user_id: UUID
    removed_motor: MotorRead
    installed_motor: MotorRead
    target_equipment: EquipmentRead | None = None
    registered_by_user: UserSummary | None = None
