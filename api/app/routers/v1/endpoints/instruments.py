from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.routers.deps import require_permission
from app.db.database import get_db
from app.core.permissions import PermissionName
from app.schemas.common import MessageResponse
from app.schemas.instrument import InstrumentCreate, InstrumentRead, InstrumentUpdate
from app.services.instruments import InstrumentService


router = APIRouter(prefix="/instruments", tags=["Instruments"])


@router.get("", response_model=list[InstrumentRead])
def list_instruments(
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(PermissionName.VIEW_AREA_DATA)),
):
    return InstrumentService(db).list_instruments(current_user)


@router.get("/{instrument_id}", response_model=InstrumentRead)
def get_instrument(
    instrument_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(PermissionName.VIEW_AREA_DATA)),
):
    return InstrumentService(db).get_instrument(instrument_id, current_user)


@router.post("", response_model=InstrumentRead, status_code=status.HTTP_201_CREATED)
def create_instrument(
    payload: InstrumentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(PermissionName.MANAGE_AREA_DATA)),
):
    return InstrumentService(db).create_instrument(payload, current_user)


@router.put("/{instrument_id}", response_model=InstrumentRead)
def update_instrument(
    instrument_id: UUID,
    payload: InstrumentUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(PermissionName.MANAGE_AREA_DATA)),
):
    return InstrumentService(db).update_instrument(instrument_id, payload, current_user)


@router.delete("/{instrument_id}", response_model=MessageResponse)
def delete_instrument(
    instrument_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(PermissionName.DELETE_AREA_DATA)),
):
    InstrumentService(db).delete_instrument(instrument_id, current_user)
    return MessageResponse(message="Instrument deleted successfully.")

