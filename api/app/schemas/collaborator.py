from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel

from app.core.enums import RecordStatus
from app.schemas.area import AreaRead
from app.schemas.common import IDSchema, TimestampSchema
from app.schemas.user import UserSummary


class CollaboratorBase(BaseModel):
    full_name: str
    registration_number: str
    job_title: str | None = None
    contact_phone: str | None = None
    status: RecordStatus = RecordStatus.ACTIVE
    area_id: UUID
    linked_user_id: UUID | None = None


class CollaboratorCreate(CollaboratorBase):
    pass


class CollaboratorUpdate(BaseModel):
    full_name: str | None = None
    registration_number: str | None = None
    job_title: str | None = None
    contact_phone: str | None = None
    status: RecordStatus | None = None
    area_id: UUID | None = None
    linked_user_id: UUID | None = None


class CollaboratorRead(CollaboratorBase, IDSchema, TimestampSchema):
    area: AreaRead | None = None
    linked_user: UserSummary | None = None

