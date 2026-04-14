from __future__ import annotations

from pydantic import BaseModel

from app.core.enums import AreaCode
from app.schemas.common import IDSchema, TimestampSchema


class AreaBase(BaseModel):
    name: str
    code: AreaCode
    description: str | None = None


class AreaCreate(AreaBase):
    pass


class AreaUpdate(BaseModel):
    name: str | None = None
    code: AreaCode | None = None
    description: str | None = None


class AreaRead(AreaBase, IDSchema, TimestampSchema):
    pass

