from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.permissions import (
    PermissionName,
    ensure_permission,
    ensure_permission_in_area,
)
from app.models.user import User
from app.db.repositories.collaborators import CollaboratorRepository
from app.services.audit import AuditService


class CollaboratorService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = CollaboratorRepository(db)
        self.audit_service = AuditService(db)

    def list_collaborators(self, current_user: User):
        ensure_permission(current_user, PermissionName.MANAGE_AREA_DATA)
        return self.repository.list_visible(current_user)

    def get_collaborator(self, collaborator_id, actor: User):
        collaborator = self.repository.get(collaborator_id)
        if not collaborator:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Collaborator not found.",
            )
        ensure_permission_in_area(actor, PermissionName.MANAGE_AREA_DATA, collaborator.area_id)
        return collaborator

    def create_collaborator(self, data, actor: User):
        ensure_permission_in_area(actor, PermissionName.MANAGE_AREA_DATA, data.area_id)
        collaborator = self.repository.create(data.model_dump())
        self.audit_service.record(
            actor=actor,
            entity_name="Collaborator",
            entity_id=str(collaborator.id),
            action="created",
            area_id=collaborator.area_id,
            summary=f"Collaborator {collaborator.full_name} created.",
            payload=data.model_dump(),
        )
        self.db.commit()
        return self.repository.get(collaborator.id)

    def update_collaborator(self, collaborator_id, data, actor: User):
        collaborator = self.get_collaborator(collaborator_id, actor)
        payload = data.model_dump(exclude_unset=True)
        ensure_permission_in_area(
            actor,
            PermissionName.MANAGE_AREA_DATA,
            payload.get("area_id", collaborator.area_id),
        )
        updated = self.repository.update(collaborator, payload)
        self.audit_service.record(
            actor=actor,
            entity_name="Collaborator",
            entity_id=str(updated.id),
            action="updated",
            area_id=updated.area_id,
            summary=f"Collaborator {updated.full_name} updated.",
            payload=payload,
        )
        self.db.commit()
        return self.repository.get(updated.id)

    def delete_collaborator(self, collaborator_id, actor: User):
        ensure_permission(actor, PermissionName.MANAGE_USERS)
        collaborator = self.get_collaborator(collaborator_id, actor)
        self.audit_service.record(
            actor=actor,
            entity_name="Collaborator",
            entity_id=str(collaborator.id),
            action="deleted",
            area_id=collaborator.area_id,
            summary=f"Collaborator {collaborator.full_name} deleted.",
        )
        self.repository.delete(collaborator)
        self.db.commit()

