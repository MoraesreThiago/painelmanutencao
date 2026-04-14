from __future__ import annotations

from pydantic import BaseModel
from uuid import UUID

from app.schemas.area import AreaRead
from app.schemas.common import IDSchema, TimestampSchema


class LocationBase(BaseModel):
    name: str
    sector: str
    description: str | None = None
    area_id: UUID


class LocationCreate(LocationBase):
    pass


class LocationUpdate(BaseModel):
    name: str | None = None
    sector: str | None = None
    description: str | None = None
    area_id: UUID | None = None


class LocationRead(LocationBase, IDSchema, TimestampSchema):
    area: AreaRead | None = None
