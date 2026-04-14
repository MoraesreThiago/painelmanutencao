from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.schemas.common import IDSchema, TimestampSchema
from app.schemas.equipment import EquipmentRead
from app.schemas.location import LocationRead
from app.schemas.user import UserSummary


class MovementBase(BaseModel):
    equipment_id: UUID
    new_location_id: UUID | None = None
    reason: str
    status_after: str | None = None
    notes: str | None = None
    moved_at: datetime | None = None


class MovementCreate(MovementBase):
    pass


class MovementUpdate(BaseModel):
    new_location_id: UUID | None = None
    reason: str | None = None
    status_after: str | None = None
    notes: str | None = None
    moved_at: datetime | None = None


class MovementRead(MovementBase, IDSchema, TimestampSchema):
    previous_location_id: UUID | None = None
    moved_by_user_id: UUID
    equipment: EquipmentRead
    previous_location: LocationRead | None = None
    new_location: LocationRead | None = None
    moved_by_user: UserSummary | None = None
