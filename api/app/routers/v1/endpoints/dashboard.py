from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.routers.deps import require_permission
from app.db.database import get_db
from app.core.permissions import PermissionName
from app.schemas.dashboard import DashboardRead
from app.services.dashboard import DashboardService


router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("", response_model=DashboardRead)
def get_dashboard(
    db: Session = Depends(get_db),
    area_id: UUID | None = Query(default=None),
    current_user=Depends(require_permission(PermissionName.VIEW_DASHBOARD)),
):
    return DashboardService(db).build_dashboard(current_user, area_id=area_id)

