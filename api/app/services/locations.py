from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.permissions import PermissionName, ensure_permission, ensure_permission_in_area
from app.models.user import User
from app.db.repositories.locations import LocationRepository
from app.services.audit import AuditService


class LocationService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = LocationRepository(db)
        self.audit_service = AuditService(db)

    def list_locations(self, current_user: User):
        ensure_permission(current_user, PermissionName.VIEW_AREA_DATA)
        return self.repository.list_visible(current_user)

    def get_location(self, location_id, actor: User):
        location = self.repository.get(location_id)
        if not location:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found.")
        ensure_permission_in_area(actor, PermissionName.VIEW_AREA_DATA, location.area_id)
        return location

    def create_location(self, data, actor: User):
        ensure_permission_in_area(actor, PermissionName.MANAGE_LOCATIONS, data.area_id)
        location = self.repository.create(data.model_dump())
        self.audit_service.record(
            actor=actor,
            entity_name="Location",
            entity_id=str(location.id),
            action="created",
            area_id=location.area_id,
            summary=f"Location {location.name} created.",
            payload=data.model_dump(),
        )
        self.db.commit()
        return self.repository.get(location.id)

    def update_location(self, location_id, data, actor: User):
        location = self.get_location(location_id, actor)
        payload = data.model_dump(exclude_unset=True)
        ensure_permission_in_area(
            actor,
            PermissionName.MANAGE_LOCATIONS,
            payload.get("area_id", location.area_id),
        )
        updated = self.repository.update(location, payload)
        self.audit_service.record(
            actor=actor,
            entity_name="Location",
            entity_id=str(updated.id),
            action="updated",
            area_id=updated.area_id,
            summary=f"Location {updated.name} updated.",
            payload=payload,
        )
        self.db.commit()
        return self.repository.get(updated.id)

    def delete_location(self, location_id, actor: User):
        location = self.get_location(location_id, actor)
        ensure_permission_in_area(actor, PermissionName.MANAGE_LOCATIONS, location.area_id)
        self.audit_service.record(
            actor=actor,
            entity_name="Location",
            entity_id=str(location.id),
            action="deleted",
            area_id=location.area_id,
            summary=f"Location {location.name} deleted.",
        )
        self.repository.delete(location)
        self.db.commit()

