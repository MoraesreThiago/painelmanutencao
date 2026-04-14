from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.routers.deps import require_permission
from app.db.database import get_db
from app.core.permissions import PermissionName
from app.schemas.role import RoleRead
from app.services.roles import RoleService


router = APIRouter(prefix="/roles", tags=["Roles"])


@router.get("", response_model=list[RoleRead])
def list_roles(
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(PermissionName.VIEW_USERS)),
):
    return RoleService(db).list_roles()

