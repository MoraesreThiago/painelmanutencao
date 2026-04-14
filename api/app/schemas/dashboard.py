from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class DashboardMetric(BaseModel):
    label: str
    value: int


class AreaSummary(BaseModel):
    area_name: str
    equipment_count: int
    motor_count: int
    instrument_count: int


class RecentMovement(BaseModel):
    equipment_code: str
    equipment_description: str
    new_location: str | None = None
    moved_at: datetime
    moved_by: str
    reason: str


class DashboardAlert(BaseModel):
    title: str
    description: str
    severity: str


class DashboardRead(BaseModel):
    metrics: list[DashboardMetric]
    area_summary: list[AreaSummary]
    recent_movements: list[RecentMovement]
    alerts: list[DashboardAlert]
