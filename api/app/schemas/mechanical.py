from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class MechanicalMetric(BaseModel):
    label: str
    value: int


class MechanicalStatusSummary(BaseModel):
    status: str
    total: int


class MechanicalEquipmentItem(BaseModel):
    id: UUID
    code: str
    tag: str | None = None
    description: str
    sector: str
    status: str
    location_name: str | None = None


class MechanicalCollaboratorItem(BaseModel):
    id: UUID
    full_name: str
    registration_number: str
    job_title: str | None = None
    contact_phone: str | None = None
    status: str


class MechanicalRecentMovement(BaseModel):
    equipment_code: str
    equipment_description: str
    new_location: str | None = None
    moved_at: datetime
    moved_by: str
    reason: str
    status_after: str | None = None


class MechanicalOverviewRead(BaseModel):
    area_name: str
    metrics: list[MechanicalMetric]
    status_summary: list[MechanicalStatusSummary]
    equipments: list[MechanicalEquipmentItem]
    collaborators: list[MechanicalCollaboratorItem]
    recent_movements: list[MechanicalRecentMovement]
