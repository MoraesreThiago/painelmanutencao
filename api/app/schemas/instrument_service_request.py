from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.core.enums import InstrumentServiceStatus, InstrumentServiceType
from app.schemas.common import IDSchema, ORMModel, TimestampSchema
from app.schemas.instrument import InstrumentRead
from app.schemas.instrument_replacement import InstrumentReplacementRead
from app.schemas.user import UserSummary


class InstrumentServiceRequestBase(BaseModel):
    instrument_id: UUID
    instrument_replacement_id: UUID | None = None
    service_type: InstrumentServiceType
    service_status: InstrumentServiceStatus = InstrumentServiceStatus.OPEN
    requested_at: datetime | None = None
    expected_return_at: datetime | None = None
    actual_return_at: datetime | None = None
    vendor_name: str | None = None
    vendor_reference: str | None = None
    reason: str
    notes: str | None = None


class InstrumentServiceRequestCreate(InstrumentServiceRequestBase):
    pass


class InstrumentServiceRequestUpdate(BaseModel):
    service_type: InstrumentServiceType | None = None
    service_status: InstrumentServiceStatus | None = None
    requested_at: datetime | None = None
    expected_return_at: datetime | None = None
    actual_return_at: datetime | None = None
    vendor_name: str | None = None
    vendor_reference: str | None = None
    reason: str | None = None
    notes: str | None = None


class InstrumentServiceRequestRead(InstrumentServiceRequestBase, IDSchema, TimestampSchema, ORMModel):
    area_id: UUID
    registered_by_user_id: UUID
    instrument: InstrumentRead
    instrument_replacement: InstrumentReplacementRead | None = None
    registered_by_user: UserSummary | None = None

