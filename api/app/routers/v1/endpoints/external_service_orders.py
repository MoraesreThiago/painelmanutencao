from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.routers.deps import require_permission
from app.db.database import get_db
from app.core.permissions import PermissionName
from app.schemas.common import MessageResponse
from app.schemas.external_service_order import (
    ExternalServiceOrderCreate,
    ExternalServiceOrderRead,
    ExternalServiceOrderUpdate,
)
from app.services.external_service_orders import ExternalServiceOrderService


router = APIRouter(prefix="/external-service-orders", tags=["External Service Orders"])


@router.get("", response_model=list[ExternalServiceOrderRead])
def list_orders(
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(PermissionName.MANAGE_EXTERNAL_SERVICE)),
):
    return ExternalServiceOrderService(db).list_orders(current_user)


@router.get("/{order_id}", response_model=ExternalServiceOrderRead)
def get_order(
    order_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(PermissionName.MANAGE_EXTERNAL_SERVICE)),
):
    return ExternalServiceOrderService(db).get_order(order_id, current_user)


@router.post("", response_model=ExternalServiceOrderRead, status_code=status.HTTP_201_CREATED)
def create_order(
    payload: ExternalServiceOrderCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(PermissionName.MANAGE_EXTERNAL_SERVICE)),
):
    return ExternalServiceOrderService(db).create_order(payload, current_user)


@router.put("/{order_id}", response_model=ExternalServiceOrderRead)
def update_order(
    order_id: UUID,
    payload: ExternalServiceOrderUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(PermissionName.MANAGE_EXTERNAL_SERVICE)),
):
    return ExternalServiceOrderService(db).update_order(order_id, payload, current_user)


@router.delete("/{order_id}", response_model=MessageResponse)
def delete_order(
    order_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(PermissionName.MANAGE_EXTERNAL_SERVICE)),
):
    ExternalServiceOrderService(db).delete_order(order_id, current_user)
    return MessageResponse(message="External service order deleted successfully.")

