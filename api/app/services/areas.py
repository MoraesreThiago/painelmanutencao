from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.permissions import PermissionName, ensure_permission, ensure_permission_in_area
from app.models.user import User
from app.db.repositories.areas import AreaRepository
from app.services.audit import AuditService


class AreaService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = AreaRepository(db)
        self.audit_service = AuditService(db)

    def list_areas(self, current_user: User):
        ensure_permission(current_user, PermissionName.VIEW_AREA_DATA)
        return self.repository.list_visible(current_user)

    def get_area(self, area_id, actor: User):
        area = self.repository.get(area_id)
        if not area:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Area not found.")
        ensure_permission_in_area(actor, PermissionName.VIEW_AREA_DATA, area.id)
        return area

    def create_area(self, data, actor: User):
        ensure_permission(actor, PermissionName.MANAGE_AREAS)
        area = self.repository.create(data.model_dump())
        self.audit_service.record(
            actor=actor,
            entity_name="Area",
            entity_id=str(area.id),
            action="created",
            area_id=area.id,
            summary=f"Area {area.name} created.",
        )
        self.db.commit()
        self.db.refresh(area)
        return area

    def update_area(self, area_id, data, actor: User):
        ensure_permission(actor, PermissionName.MANAGE_AREAS)
        area = self.get_area(area_id, actor)
        payload = data.model_dump(exclude_unset=True)
        updated = self.repository.update(area, payload)
        self.audit_service.record(
            actor=actor,
            entity_name="Area",
            entity_id=str(updated.id),
            action="updated",
            area_id=updated.id,
            summary=f"Area {updated.name} updated.",
            payload=payload,
        )
        self.db.commit()
        self.db.refresh(updated)
        return updated

    def delete_area(self, area_id, actor: User):
        ensure_permission(actor, PermissionName.MANAGE_AREAS)
        area = self.get_area(area_id, actor)
        self.audit_service.record(
            actor=actor,
            entity_name="Area",
            entity_id=str(area.id),
            action="deleted",
            area_id=area.id,
            summary=f"Area {area.name} deleted.",
        )
        self.repository.delete(area)
        self.db.commit()

