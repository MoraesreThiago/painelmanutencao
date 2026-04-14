from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.routers.deps import require_permission
from app.db.database import get_db
from app.core.permissions import PermissionName
from app.schemas.burned_motor_record import (
    BurnedMotorRecordCreate,
    BurnedMotorRecordRead,
    BurnedMotorRecordUpdate,
)
from app.services.burned_motor_records import BurnedMotorRecordService


router = APIRouter(prefix="/burned-motors", tags=["Burned Motors"])


@router.get("", response_model=list[BurnedMotorRecordRead])
def list_burned_motors(
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(PermissionName.VIEW_AREA_DATA)),
):
    return BurnedMotorRecordService(db).list_records(current_user)


@router.get("/{record_id}", response_model=BurnedMotorRecordRead)
def get_burned_motor(
    record_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(PermissionName.VIEW_AREA_DATA)),
):
    return BurnedMotorRecordService(db).get_record(record_id, current_user)


@router.post("", response_model=BurnedMotorRecordRead, status_code=status.HTTP_201_CREATED)
def create_burned_motor(
    payload: BurnedMotorRecordCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(PermissionName.CREATE_OCCURRENCES)),
):
    return BurnedMotorRecordService(db).create_record(payload, current_user)


@router.put("/{record_id}", response_model=BurnedMotorRecordRead)
def update_burned_motor(
    record_id: UUID,
    payload: BurnedMotorRecordUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(PermissionName.EDIT_OCCURRENCES)),
):
    return BurnedMotorRecordService(db).update_record(record_id, payload, current_user)

