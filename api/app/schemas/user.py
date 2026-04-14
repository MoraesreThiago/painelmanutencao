from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.schemas.area import AreaRead
from app.schemas.common import IDSchema, ORMModel, TimestampSchema
from app.schemas.role import RoleRead


class UserSummary(ORMModel):
    id: UUID
    full_name: str
    email: EmailStr


class UserBase(BaseModel):
    full_name: str
    email: EmailStr
    registration_number: str | None = None
    job_title: str | None = None
    phone: str | None = None
    is_active: bool = True
    area_id: UUID | None = None
    area_ids: list[UUID] | None = None
    role_id: UUID


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    full_name: str | None = None
    email: EmailStr | None = None
    registration_number: str | None = None
    job_title: str | None = None
    phone: str | None = None
    is_active: bool | None = None
    area_id: UUID | None = None
    area_ids: list[UUID] | None = None
    role_id: UUID | None = None
    password: str | None = None


class UserRead(UserBase, IDSchema, TimestampSchema):
    last_login_at: datetime | None = None
    area: AreaRead | None = None
    allowed_areas: list[AreaRead] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)
    role: RoleRead
