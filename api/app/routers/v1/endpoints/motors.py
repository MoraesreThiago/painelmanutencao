from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.routers.deps import require_permission
from app.db.database import get_db
from app.core.permissions import PermissionName
from app.schemas.common import MessageResponse
from app.schemas.motor import MotorCreate, MotorRead, MotorUpdate
from app.services.motors import MotorService


router = APIRouter(prefix="/motors", tags=["Motors"])


@router.get("", response_model=list[MotorRead])
def list_motors(
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(PermissionName.VIEW_AREA_DATA)),
):
    return MotorService(db).list_motors(current_user)


@router.get("/{motor_id}", response_model=MotorRead)
def get_motor(
    motor_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(PermissionName.VIEW_AREA_DATA)),
):
    return MotorService(db).get_motor(motor_id, current_user)


@router.post("", response_model=MotorRead, status_code=status.HTTP_201_CREATED)
def create_motor(
    payload: MotorCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(PermissionName.MANAGE_AREA_DATA)),
):
    return MotorService(db).create_motor(payload, current_user)


@router.put("/{motor_id}", response_model=MotorRead)
def update_motor(
    motor_id: UUID,
    payload: MotorUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(PermissionName.MANAGE_AREA_DATA)),
):
    return MotorService(db).update_motor(motor_id, payload, current_user)


@router.delete("/{motor_id}", response_model=MessageResponse)
def delete_motor(
    motor_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(PermissionName.DELETE_AREA_DATA)),
):
    MotorService(db).delete_motor(motor_id, current_user)
    return MessageResponse(message="Motor deleted successfully.")

