from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.core.enums import EquipmentStatus, EquipmentType
from app.schemas.area import AreaRead
from app.schemas.common import IDSchema, TimestampSchema
from app.schemas.location import LocationRead


class EquipmentBase(BaseModel):
    code: str
    tag: str | None = None
    description: str
    sector: str
    manufacturer: str | None = None
    model: str | None = None
    serial_number: str | None = None
    notes: str | None = None
    type: EquipmentType = EquipmentType.GENERIC
    status: EquipmentStatus = EquipmentStatus.ACTIVE
    registered_at: datetime | None = None
    area_id: UUID
    location_id: UUID | None = None


class EquipmentCreate(EquipmentBase):
    pass


class EquipmentUpdate(BaseModel):
    code: str | None = None
    tag: str | None = None
    description: str | None = None
    sector: str | None = None
    manufacturer: str | None = None
    model: str | None = None
    serial_number: str | None = None
    notes: str | None = None
    status: EquipmentStatus | None = None
    area_id: UUID | None = None
    location_id: UUID | None = None


class EquipmentRead(EquipmentBase, IDSchema, TimestampSchema):
    area: AreaRead | None = None
    location: LocationRead | None = None

