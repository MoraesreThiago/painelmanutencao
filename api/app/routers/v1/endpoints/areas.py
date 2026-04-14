from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.routers.deps import require_permission
from app.db.database import get_db
from app.core.permissions import PermissionName
from app.schemas.area import AreaCreate, AreaRead, AreaUpdate
from app.schemas.common import MessageResponse
from app.services.areas import AreaService


router = APIRouter(prefix="/areas", tags=["Areas"])


@router.get("", response_model=list[AreaRead])
def list_areas(
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(PermissionName.VIEW_AREA_DATA)),
):
    return AreaService(db).list_areas(current_user)


@router.get("/{area_id}", response_model=AreaRead)
def get_area(
    area_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(PermissionName.VIEW_AREA_DATA)),
):
    return AreaService(db).get_area(area_id, current_user)


@router.post("", response_model=AreaRead, status_code=status.HTTP_201_CREATED)
def create_area(
    payload: AreaCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(PermissionName.MANAGE_AREAS)),
):
    return AreaService(db).create_area(payload, current_user)


@router.put("/{area_id}", response_model=AreaRead)
def update_area(
    area_id: UUID,
    payload: AreaUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(PermissionName.MANAGE_AREAS)),
):
    return AreaService(db).update_area(area_id, payload, current_user)


@router.delete("/{area_id}", response_model=MessageResponse)
def delete_area(
    area_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(PermissionName.MANAGE_AREAS)),
):
    AreaService(db).delete_area(area_id, current_user)
    return MessageResponse(message="Area deleted successfully.")

