from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.schemas.common import IDSchema, ORMModel, TimestampSchema
from app.schemas.equipment import EquipmentRead
from app.schemas.instrument import InstrumentRead
from app.schemas.user import UserSummary


class InstrumentReplacementBase(BaseModel):
    removed_instrument_id: UUID
    installed_instrument_id: UUID
    target_equipment_id: UUID | None = None
    target_equipment_tag: str
    reason: str
    replaced_at: datetime | None = None
    notes: str | None = None


class InstrumentReplacementCreate(InstrumentReplacementBase):
    pass


class InstrumentReplacementRead(InstrumentReplacementBase, IDSchema, TimestampSchema, ORMModel):
    area_id: UUID
    registered_by_user_id: UUID
    removed_instrument: InstrumentRead
    installed_instrument: InstrumentRead
    target_equipment: EquipmentRead | None = None
    registered_by_user: UserSummary | None = None
