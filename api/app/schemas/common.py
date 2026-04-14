from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class IDSchema(ORMModel):
    id: UUID


class TimestampSchema(ORMModel):
    created_at: datetime
    updated_at: datetime


class MessageResponse(BaseModel):
    message: str
