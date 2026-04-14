from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.routers.deps import require_permission
from app.db.database import get_db
from app.core.permissions import PermissionName
from app.schemas.common import MessageResponse
from app.schemas.location import LocationCreate, LocationRead, LocationUpdate
from app.services.locations import LocationService


router = APIRouter(prefix="/locations", tags=["Locations"])


@router.get("", response_model=list[LocationRead])
def list_locations(
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(PermissionName.VIEW_AREA_DATA)),
):
    return LocationService(db).list_locations(current_user)


@router.post("", response_model=LocationRead, status_code=status.HTTP_201_CREATED)
def create_location(
    payload: LocationCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(PermissionName.MANAGE_LOCATIONS)),
):
    return LocationService(db).create_location(payload, current_user)


@router.put("/{location_id}", response_model=LocationRead)
def update_location(
    location_id: UUID,
    payload: LocationUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(PermissionName.MANAGE_LOCATIONS)),
):
    return LocationService(db).update_location(location_id, payload, current_user)


@router.delete("/{location_id}", response_model=MessageResponse)
def delete_location(
    location_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(PermissionName.MANAGE_LOCATIONS)),
):
    LocationService(db).delete_location(location_id, current_user)
    return MessageResponse(message="Location deleted successfully.")

