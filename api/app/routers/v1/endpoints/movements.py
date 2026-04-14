from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.routers.deps import require_permission
from app.db.database import get_db
from app.core.permissions import PermissionName
from app.schemas.common import MessageResponse
from app.schemas.movement import MovementCreate, MovementRead
from app.services.movements import MovementService


router = APIRouter(prefix="/movements", tags=["Movements"])


@router.get("", response_model=list[MovementRead])
def list_movements(
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(PermissionName.VIEW_AREA_DATA)),
):
    return MovementService(db).list_movements(current_user)


@router.get("/{movement_id}", response_model=MovementRead)
def get_movement(
    movement_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(PermissionName.VIEW_AREA_DATA)),
):
    return MovementService(db).get_movement(movement_id, current_user)


@router.post("", response_model=MovementRead, status_code=status.HTTP_201_CREATED)
def create_movement(
    payload: MovementCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(PermissionName.CREATE_OCCURRENCES)),
):
    return MovementService(db).create_movement(payload, current_user)


@router.delete("/{movement_id}", response_model=MessageResponse)
def delete_movement(
    movement_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(PermissionName.DELETE_OCCURRENCES)),
):
    MovementService(db).delete_movement(movement_id, current_user)
    return MessageResponse(message="Movement deleted successfully.")

