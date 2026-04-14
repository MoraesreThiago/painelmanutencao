from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.routers.deps import require_permission
from app.db.database import get_db
from app.core.permissions import PermissionName
from app.schemas.instrument_service_request import (
    InstrumentServiceRequestCreate,
    InstrumentServiceRequestRead,
    InstrumentServiceRequestUpdate,
)
from app.services.instrument_service_requests import InstrumentServiceRequestService


router = APIRouter(prefix="/instrument-service-requests", tags=["Instrument Service Requests"])


@router.get("", response_model=list[InstrumentServiceRequestRead])
def list_instrument_service_requests(
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(PermissionName.VIEW_AREA_DATA)),
):
    return InstrumentServiceRequestService(db).list_requests(current_user)


@router.get("/{request_id}", response_model=InstrumentServiceRequestRead)
def get_instrument_service_request(
    request_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(PermissionName.VIEW_AREA_DATA)),
):
    return InstrumentServiceRequestService(db).get_request(request_id, current_user)


@router.post("", response_model=InstrumentServiceRequestRead, status_code=status.HTTP_201_CREATED)
def create_instrument_service_request(
    payload: InstrumentServiceRequestCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(PermissionName.CREATE_OCCURRENCES)),
):
    return InstrumentServiceRequestService(db).create_request(payload, current_user)


@router.put("/{request_id}", response_model=InstrumentServiceRequestRead)
def update_instrument_service_request(
    request_id: UUID,
    payload: InstrumentServiceRequestUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(PermissionName.EDIT_OCCURRENCES)),
):
    return InstrumentServiceRequestService(db).update_request(request_id, payload, current_user)

