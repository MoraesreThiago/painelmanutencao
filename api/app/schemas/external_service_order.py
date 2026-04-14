from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.core.enums import ExternalServiceStatus
from app.schemas.common import IDSchema, TimestampSchema
from app.schemas.motor import MotorRead
from app.schemas.user import UserSummary


class ExternalServiceOrderBase(BaseModel):
    motor_id: UUID
    sent_at: datetime | None = None
    reason: str
    vendor_name: str
    work_order_number: str
    authorized_by_user_id: UUID
    expected_return_at: datetime | None = None
    actual_return_at: datetime | None = None
    service_status: ExternalServiceStatus = ExternalServiceStatus.OPEN
    notes: str | None = None
    attachments_metadata: dict | None = None


class ExternalServiceOrderCreate(ExternalServiceOrderBase):
    pass


class ExternalServiceOrderUpdate(BaseModel):
    sent_at: datetime | None = None
    reason: str | None = None
    vendor_name: str | None = None
    work_order_number: str | None = None
    authorized_by_user_id: UUID | None = None
    expected_return_at: datetime | None = None
    actual_return_at: datetime | None = None
    service_status: ExternalServiceStatus | None = None
    notes: str | None = None
    attachments_metadata: dict | None = None


class ExternalServiceOrderRead(ExternalServiceOrderBase, IDSchema, TimestampSchema):
    registered_by_user_id: UUID
    motor: MotorRead
    authorized_by_user: UserSummary | None = None
    registered_by_user: UserSummary | None = None

