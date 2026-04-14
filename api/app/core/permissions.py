from __future__ import annotations

from enum import Enum
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import Select, false

from app.core.enums import RoleName
from app.models.user import User


class PermissionName(str, Enum):
    VIEW_DASHBOARD = "view_dashboard"
    VIEW_GLOBAL_DASHBOARD = "view_global_dashboard"
    VIEW_AREA_DATA = "view_area_data"
    MANAGE_AREA_DATA = "manage_area_data"
    DELETE_AREA_DATA = "delete_area_data"
    CREATE_OCCURRENCES = "create_occurrences"
    EDIT_OCCURRENCES = "edit_occurrences"
    REVIEW_OCCURRENCES = "review_occurrences"
    DELETE_OCCURRENCES = "delete_occurrences"
    VIEW_REPORTS = "view_reports"
    VIEW_GLOBAL_REPORTS = "view_global_reports"
    VIEW_USERS = "view_users"
    MANAGE_USERS = "manage_users"
    MANAGE_AREAS = "manage_areas"
    MANAGE_LOCATIONS = "manage_locations"
    MANAGE_EXTERNAL_SERVICE = "manage_external_service"
    VIEW_ALL_AREAS = "view_all_areas"
    ASSIGN_GLOBAL_ROLES = "assign_global_roles"
    ASSUME_AREA_CONTEXT = "assume_area_context"


ACTIVE_ROLE_NAMES = (
    RoleName.MANUTENTOR,
    RoleName.LIDER,
    RoleName.SUPERVISOR,
    RoleName.GERENTE,
    RoleName.ADMIN,
)
GLOBAL_ROLES = {RoleName.ADMIN, RoleName.GERENTE}
LEGACY_ROLE_ALIASES = {RoleName.INSPETOR: RoleName.LIDER}
ROLE_INCREMENTS: dict[RoleName, set[PermissionName]] = {
    RoleName.MANUTENTOR: {
        PermissionName.VIEW_DASHBOARD,
        PermissionName.VIEW_AREA_DATA,
        PermissionName.CREATE_OCCURRENCES,
        PermissionName.EDIT_OCCURRENCES,
    },
    RoleName.LIDER: {
        PermissionName.VIEW_REPORTS,
        PermissionName.MANAGE_AREA_DATA,
        PermissionName.MANAGE_EXTERNAL_SERVICE,
    },
    RoleName.SUPERVISOR: {
        PermissionName.REVIEW_OCCURRENCES,
        PermissionName.DELETE_OCCURRENCES,
        PermissionName.DELETE_AREA_DATA,
        PermissionName.MANAGE_LOCATIONS,
        PermissionName.VIEW_USERS,
    },
    RoleName.GERENTE: {
        PermissionName.VIEW_GLOBAL_DASHBOARD,
        PermissionName.VIEW_GLOBAL_REPORTS,
        PermissionName.MANAGE_AREAS,
        PermissionName.VIEW_ALL_AREAS,
    },
    RoleName.ADMIN: {
        PermissionName.MANAGE_USERS,
        PermissionName.ASSIGN_GLOBAL_ROLES,
        PermissionName.ASSUME_AREA_CONTEXT,
    },
}


def normalize_role_name(role_name: RoleName) -> RoleName:
    return LEGACY_ROLE_ALIASES.get(role_name, role_name)


def get_role_name(user: User) -> RoleName:
    return normalize_role_name(RoleName(user.role.name))


def is_business_role(role_name: RoleName) -> bool:
    return normalize_role_name(role_name) in ACTIVE_ROLE_NAMES


def permissions_for_role(role_name: RoleName) -> set[PermissionName]:
    normalized_role = normalize_role_name(role_name)
    granted: set[PermissionName] = set()
    for level in ACTIVE_ROLE_NAMES:
        granted.update(ROLE_INCREMENTS[level])
        if level == normalized_role:
            break
    return granted


def get_user_permissions(user: User) -> set[PermissionName]:
    return permissions_for_role(get_role_name(user))


def has_permission(user: User, permission: PermissionName) -> bool:
    return permission in get_user_permissions(user)


def has_any_permission(user: User, *permissions: PermissionName) -> bool:
    granted = get_user_permissions(user)
    return any(permission in granted for permission in permissions)


def is_global_user(user: User) -> bool:
    return get_role_name(user) in GLOBAL_ROLES


def get_user_area_ids(user: User) -> set[UUID]:
    return {area_id for area_id in user.area_ids if area_id is not None}


def has_area_access(user: User, area_id: UUID | None) -> bool:
    if area_id is None:
        return is_global_user(user)
    if is_global_user(user):
        return True
    return area_id in get_user_area_ids(user)


def ensure_permission(user: User, permission: PermissionName) -> None:
    if has_permission(user, permission):
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="User does not have permission for this action.",
    )


def ensure_any_permission(user: User, *permissions: PermissionName) -> None:
    if has_any_permission(user, *permissions):
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="User does not have permission for this action.",
    )


def ensure_area_access(user: User, area_id: UUID | None) -> None:
    if has_area_access(user, area_id):
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="User does not have permission for the requested area.",
    )


def ensure_permission_in_area(user: User, permission: PermissionName, area_id: UUID | None) -> None:
    ensure_permission(user, permission)
    ensure_area_access(user, area_id)


def can_manage_users(user: User) -> bool:
    return has_permission(user, PermissionName.MANAGE_USERS)


def can_view_users(user: User) -> bool:
    return has_permission(user, PermissionName.VIEW_USERS) or can_manage_users(user)


def can_view_reports(user: User) -> bool:
    return has_permission(user, PermissionName.VIEW_REPORTS) or has_permission(
        user,
        PermissionName.VIEW_GLOBAL_REPORTS,
    )


def can_view_global_reports(user: User) -> bool:
    return has_permission(user, PermissionName.VIEW_GLOBAL_REPORTS)


def can_view_occurrence(user: User, area_id: UUID | None) -> bool:
    return has_permission(user, PermissionName.VIEW_AREA_DATA) and has_area_access(user, area_id)


def can_edit_occurrence(user: User, area_id: UUID | None) -> bool:
    return has_permission(user, PermissionName.EDIT_OCCURRENCES) and has_area_access(user, area_id)


def can_manage_external_service(user: User, area_id: UUID | None) -> bool:
    return has_permission(user, PermissionName.MANAGE_EXTERNAL_SERVICE) and has_area_access(user, area_id)


def apply_area_scope(query: Select, user: User, model: type) -> Select:
    if is_global_user(user) or not hasattr(model, "area_id"):
        return query

    area_ids = get_user_area_ids(user)
    if not area_ids:
        return query.where(false())
    return query.where(model.area_id.in_(area_ids))


def apply_area_id_scope(query: Select, user: User, area_column) -> Select:
    if is_global_user(user):
        return query

    area_ids = get_user_area_ids(user)
    if not area_ids:
        return query.where(false())
    return query.where(area_column.in_(area_ids))

