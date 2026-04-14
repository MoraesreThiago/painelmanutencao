from __future__ import annotations

from pydantic import BaseModel

from app.core.enums import RoleName
from app.schemas.common import IDSchema, TimestampSchema


class RoleBase(BaseModel):
    name: RoleName
    description: str | None = None


class RoleRead(RoleBase, IDSchema, TimestampSchema):
    pass

