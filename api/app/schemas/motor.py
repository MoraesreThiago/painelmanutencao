from __future__ import annotations

from datetime import date
from uuid import UUID

from pydantic import BaseModel

from app.core.enums import MotorStatus
from app.schemas.common import ORMModel
from app.schemas.equipment import EquipmentBase, EquipmentRead


class MotorCreate(EquipmentBase):
    unique_identifier: str
    current_status: MotorStatus = MotorStatus.IN_OPERATION
    last_internal_service_at: date | None = None


class MotorUpdate(BaseModel):
    code: str | None = None
    tag: str | None = None
    description: str | None = None
    sector: str | None = None
    manufacturer: str | None = None
    model: str | None = None
    serial_number: str | None = None
    notes: str | None = None
    status: str | None = None
    area_id: UUID | None = None
    location_id: UUID | None = None
    unique_identifier: str | None = None
    current_status: MotorStatus | None = None
    last_internal_service_at: date | None = None


class MotorRead(ORMModel):
    equipment_id: UUID
    unique_identifier: str
    current_status: MotorStatus
    last_internal_service_at: date | None = None
    equipment: EquipmentRead

