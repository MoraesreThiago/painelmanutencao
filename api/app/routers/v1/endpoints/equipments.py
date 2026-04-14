from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.routers.deps import require_permission
from app.db.database import get_db
from app.core.permissions import PermissionName
from app.schemas.common import MessageResponse
from app.schemas.equipment import EquipmentCreate, EquipmentRead, EquipmentUpdate
from app.services.equipments import EquipmentService


router = APIRouter(prefix="/equipments", tags=["Equipments"])


@router.get("", response_model=list[EquipmentRead])
def list_equipments(
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(PermissionName.VIEW_AREA_DATA)),
):
    return EquipmentService(db).list_equipments(current_user)


@router.get("/{equipment_id}", response_model=EquipmentRead)
def get_equipment(
    equipment_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(PermissionName.VIEW_AREA_DATA)),
):
    return EquipmentService(db).get_equipment(equipment_id, current_user)


@router.post("", response_model=EquipmentRead, status_code=status.HTTP_201_CREATED)
def create_equipment(
    payload: EquipmentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(PermissionName.MANAGE_AREA_DATA)),
):
    return EquipmentService(db).create_equipment(payload, current_user)


@router.put("/{equipment_id}", response_model=EquipmentRead)
def update_equipment(
    equipment_id: UUID,
    payload: EquipmentUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(PermissionName.MANAGE_AREA_DATA)),
):
    return EquipmentService(db).update_equipment(equipment_id, payload, current_user)


@router.delete("/{equipment_id}", response_model=MessageResponse)
def delete_equipment(
    equipment_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(PermissionName.DELETE_AREA_DATA)),
):
    EquipmentService(db).delete_equipment(equipment_id, current_user)
    return MessageResponse(message="Equipment deleted successfully.")

