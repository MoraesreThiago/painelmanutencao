from __future__ import annotations

from datetime import date
from uuid import UUID

from pydantic import BaseModel

from app.core.enums import InstrumentStatus
from app.schemas.common import ORMModel
from app.schemas.equipment import EquipmentBase, EquipmentRead


class InstrumentCreate(EquipmentBase):
    unique_identifier: str
    instrument_type: str
    current_status: InstrumentStatus = InstrumentStatus.IN_STOCK
    calibration_due_date: date | None = None


class InstrumentUpdate(BaseModel):
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
    instrument_type: str | None = None
    current_status: InstrumentStatus | None = None
    calibration_due_date: date | None = None


class InstrumentRead(ORMModel):
    equipment_id: UUID
    unique_identifier: str
    instrument_type: str
    current_status: InstrumentStatus
    calibration_due_date: date | None = None
    equipment: EquipmentRead

