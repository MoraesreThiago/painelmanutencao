from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.routers.deps import require_permission
from app.db.database import get_db
from app.core.permissions import PermissionName
from app.schemas.mechanical import MechanicalOverviewRead
from app.services.mechanical import MechanicalService


router = APIRouter(prefix="/mechanical", tags=["Mechanical"])


@router.get("/overview", response_model=MechanicalOverviewRead)
def get_mechanical_overview(
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(PermissionName.VIEW_AREA_DATA)),
):
    return MechanicalService(db).build_overview(current_user)

