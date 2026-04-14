from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.routers.deps import require_permission
from app.db.database import get_db
from app.core.permissions import PermissionName
from app.schemas.motor_replacement import MotorReplacementCreate, MotorReplacementRead
from app.services.motor_replacements import MotorReplacementService


router = APIRouter(prefix="/motor-replacements", tags=["Motor Replacements"])


@router.get("", response_model=list[MotorReplacementRead])
def list_motor_replacements(
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(PermissionName.VIEW_AREA_DATA)),
):
    return MotorReplacementService(db).list_replacements(current_user)


@router.get("/{replacement_id}", response_model=MotorReplacementRead)
def get_motor_replacement(
    replacement_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(PermissionName.VIEW_AREA_DATA)),
):
    return MotorReplacementService(db).get_replacement(replacement_id, current_user)


@router.post("", response_model=MotorReplacementRead, status_code=status.HTTP_201_CREATED)
def create_motor_replacement(
    payload: MotorReplacementCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(PermissionName.CREATE_OCCURRENCES)),
):
    return MotorReplacementService(db).create_replacement(payload, current_user)

