from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.routers.deps import require_permission
from app.db.database import get_db
from app.core.permissions import PermissionName
from app.schemas.instrument_replacement import InstrumentReplacementCreate, InstrumentReplacementRead
from app.services.instrument_replacements import InstrumentReplacementService


router = APIRouter(prefix="/instrument-replacements", tags=["Instrument Replacements"])


@router.get("", response_model=list[InstrumentReplacementRead])
def list_instrument_replacements(
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(PermissionName.VIEW_AREA_DATA)),
):
    return InstrumentReplacementService(db).list_replacements(current_user)


@router.get("/{replacement_id}", response_model=InstrumentReplacementRead)
def get_instrument_replacement(
    replacement_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(PermissionName.VIEW_AREA_DATA)),
):
    return InstrumentReplacementService(db).get_replacement(replacement_id, current_user)


@router.post("", response_model=InstrumentReplacementRead, status_code=status.HTTP_201_CREATED)
def create_instrument_replacement(
    payload: InstrumentReplacementCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(PermissionName.CREATE_OCCURRENCES)),
):
    return InstrumentReplacementService(db).create_replacement(payload, current_user)

