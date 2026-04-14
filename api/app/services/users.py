from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.core.enums import RoleName
from app.core.permissions import (
    GLOBAL_ROLES,
    PermissionName,
    can_manage_users,
    ensure_area_access,
    ensure_permission,
    get_role_name,
    get_user_area_ids,
    is_global_user,
    normalize_role_name,
)
from app.models.user_area import UserArea
from app.models.area import Area
from app.models.user import User
from app.db.repositories.areas import AreaRepository
from app.db.repositories.roles import RoleRepository
from app.db.repositories.users import UserRepository
from app.services.audit import AuditService


class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = UserRepository(db)
        self.area_repository = AreaRepository(db)
        self.role_repository = RoleRepository(db)
        self.audit_service = AuditService(db)

    def list_users(self, current_user: User):
        ensure_permission(current_user, PermissionName.VIEW_USERS)
        return self.repository.list_visible(current_user)

    def get_user(self, user_id, actor: User):
        ensure_permission(actor, PermissionName.VIEW_USERS)
        user = self.repository.get(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        self._ensure_user_visibility(actor, user)
        return user

    def _validate_role_assignment(self, *, actor: User, role_id, area_id, area_ids: list | None):
        role = self.role_repository.get(role_id)
        if not role:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found.")

        actor_role = get_role_name(actor)
        target_role = normalize_role_name(RoleName(role.name))
        requested_area_ids = self._normalize_area_ids(area_id=area_id, area_ids=area_ids)

        if target_role in GLOBAL_ROLES and actor_role != RoleName.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can assign global roles.",
            )

        if target_role not in GLOBAL_ROLES:
            if not requested_area_ids:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Operational roles must be linked to at least one area.",
                )
            self._validate_area_assignments(actor, requested_area_ids)

        return role, requested_area_ids

    @staticmethod
    def _normalize_area_ids(*, area_id, area_ids: list | None) -> list:
        normalized_ids: list = []
        for value in list(area_ids or []):
            if value and value not in normalized_ids:
                normalized_ids.append(value)
        if area_id and area_id not in normalized_ids:
            normalized_ids.insert(0, area_id)
        return normalized_ids

    def _validate_area_assignments(self, actor: User, area_ids: list) -> list[Area]:
        areas: list[Area] = []
        for area_id in area_ids:
            area = self.area_repository.get(area_id)
            if not area:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Area not found.")
            ensure_area_access(actor, area_id)
            areas.append(area)
        return areas

    def _sync_area_assignments(self, user: User, area_ids: list) -> None:
        target_ids = list(dict.fromkeys(area_ids))
        current_assignments = {assignment.area_id: assignment for assignment in user.area_assignments}

        for area_id, assignment in list(current_assignments.items()):
            if area_id not in target_ids:
                self.db.delete(assignment)

        for area_id in target_ids:
            if area_id not in current_assignments:
                self.db.add(UserArea(user_id=user.id, area_id=area_id))

        user.area_id = target_ids[0] if target_ids else None
        self.db.add(user)
        self.db.flush()

    @staticmethod
    def _user_area_overlap(actor: User, target_user: User) -> bool:
        actor_area_ids = get_user_area_ids(actor)
        target_area_ids = get_user_area_ids(target_user)
        return bool(actor_area_ids & target_area_ids)

    def _ensure_user_visibility(self, actor: User, target_user: User) -> None:
        if can_manage_users(actor) or is_global_user(actor):
            return
        if not self._user_area_overlap(actor, target_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User does not have permission for the requested area.",
            )

    def create_user(self, data, actor: User):
        ensure_permission(actor, PermissionName.MANAGE_USERS)
        _, requested_area_ids = self._validate_role_assignment(
            actor=actor,
            role_id=data.role_id,
            area_id=data.area_id,
            area_ids=data.area_ids,
        )
        payload = data.model_dump(exclude={"password", "area_ids"})
        payload["area_id"] = requested_area_ids[0] if requested_area_ids else payload.get("area_id")
        payload["password_hash"] = get_password_hash(data.password)
        user = self.repository.create(payload)
        self._sync_area_assignments(user, requested_area_ids)
        self.audit_service.record(
            actor=actor,
            entity_name="User",
            entity_id=str(user.id),
            action="created",
            area_id=user.area_id,
            summary=f"User {user.full_name} created.",
            payload=payload,
        )
        self.db.commit()
        self.db.expire_all()
        return self.repository.get(user.id)

    def update_user(self, user_id, data, actor: User):
        ensure_permission(actor, PermissionName.MANAGE_USERS)
        user = self.get_user(user_id, actor)
        payload = data.model_dump(exclude_unset=True, exclude={"password", "area_ids"})
        requested_area_ids = self._normalize_area_ids(
            area_id=payload.get("area_id", user.area_id),
            area_ids=data.area_ids if "area_ids" in data.model_fields_set else user.area_ids,
        )
        target_area_id = requested_area_ids[0] if requested_area_ids else None
        target_role_id = payload.get("role_id", user.role_id)
        self._validate_role_assignment(
            actor=actor,
            role_id=target_role_id,
            area_id=target_area_id,
            area_ids=requested_area_ids,
        )

        if "password" in data.model_fields_set and data.password:
            payload["password_hash"] = get_password_hash(data.password)

        payload["area_id"] = target_area_id
        updated = self.repository.update(user, payload)
        self._sync_area_assignments(updated, requested_area_ids)
        self.audit_service.record(
            actor=actor,
            entity_name="User",
            entity_id=str(updated.id),
            action="updated",
            area_id=updated.area_id,
            summary=f"User {updated.full_name} updated.",
            payload=payload,
        )
        self.db.commit()
        self.db.expire_all()
        return self.repository.get(updated.id)

    def delete_user(self, user_id, actor: User):
        ensure_permission(actor, PermissionName.MANAGE_USERS)
        user = self.get_user(user_id, actor)
        self.audit_service.record(
            actor=actor,
            entity_name="User",
            entity_id=str(user.id),
            action="deleted",
            area_id=user.area_id,
            summary=f"User {user.full_name} deleted.",
        )
        self.repository.delete(user)
        self.db.commit()

