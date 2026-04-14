from __future__ import annotations

from datetime import datetime
from uuid import UUID

from app.core.enums import NotificationStatus
from app.schemas.common import IDSchema, TimestampSchema


class NotificationEventRead(IDSchema, TimestampSchema):
    event_type: str
    entity_name: str
    entity_id: str
    area_id: UUID | None = None
    status: NotificationStatus
    payload: dict | None = None
    processing_attempts: int
    occurred_at: datetime
    last_attempted_at: datetime | None = None
    processed_at: datetime | None = None
    last_error: str | None = None

