from __future__ import annotations

from enum import Enum

from django.core.exceptions import PermissionDenied
from django.urls import reverse

from common.enums import AreaCode, RoleName


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
    RoleName.INSPETOR,
    RoleName.LIDER,
    RoleName.SUPERVISOR,
    RoleName.GERENTE,
    RoleName.ADMIN,
)
GLOBAL_ROLES = {RoleName.ADMIN, RoleName.GERENTE}
LEGACY_ROLE_ALIASES: dict[RoleName, RoleName] = {}
ASSUMABLE_ROLE_NAMES = (
    RoleName.MANUTENTOR,
    RoleName.INSPETOR,
    RoleName.LIDER,
    RoleName.SUPERVISOR,
    RoleName.GERENTE,
)
ROLE_INCREMENTS: dict[RoleName, set[PermissionName]] = {
    RoleName.MANUTENTOR: {
        PermissionName.VIEW_DASHBOARD,
        PermissionName.VIEW_AREA_DATA,
        PermissionName.CREATE_OCCURRENCES,
        PermissionName.EDIT_OCCURRENCES,
    },
    RoleName.INSPETOR: {
        PermissionName.VIEW_REPORTS,
        PermissionName.MANAGE_AREA_DATA,
        PermissionName.MANAGE_EXTERNAL_SERVICE,
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
AREA_ROUTE_MAP = {
    AreaCode.ELETRICA: "access:workspace-eletrica",
    AreaCode.MECANICA: "access:workspace-mecanica",
    AreaCode.INSTRUMENTACAO: "access:workspace-instrumentacao",
}


def normalize_role_name(role_name: str | RoleName | None) -> RoleName | None:
    if not role_name:
        return None
    normalized = RoleName(role_name)
    return LEGACY_ROLE_ALIASES.get(normalized, normalized)


def permissions_for_role(role_name: str | RoleName | None) -> set[PermissionName]:
    normalized_role = normalize_role_name(role_name)
    if not normalized_role:
        return set()

    granted: set[PermissionName] = set()
    for level in ACTIVE_ROLE_NAMES:
        granted.update(ROLE_INCREMENTS[level])
        if level == normalized_role:
            break
    return granted


def get_user_permissions(user) -> set[PermissionName]:
    return permissions_for_role(get_user_role_name(user))


def get_actual_user_role_name(user) -> RoleName | None:
    role_name = getattr(getattr(user, "role", None), "name", None)
    return normalize_role_name(role_name)


def get_assumed_user_role_name(user) -> RoleName | None:
    return normalize_role_name(getattr(user, "_assumed_role_name", None))


def get_user_role_name(user) -> RoleName | None:
    assumed_role_name = get_assumed_user_role_name(user)
    if assumed_role_name in ASSUMABLE_ROLE_NAMES:
        return normalize_role_name(assumed_role_name)
    return get_actual_user_role_name(user)


def is_assuming_role_context(user) -> bool:
    actual_role_name = get_actual_user_role_name(user)
    effective_role_name = get_user_role_name(user)
    return bool(actual_role_name and effective_role_name and actual_role_name != effective_role_name)


def is_global_user(user) -> bool:
    role_name = get_user_role_name(user)
    return role_name in GLOBAL_ROLES


def has_permission(user, permission: PermissionName) -> bool:
    return permission in get_user_permissions(user)


def has_actual_permission(user, permission: PermissionName) -> bool:
    return permission in permissions_for_role(get_actual_user_role_name(user))


def ensure_permission(user, permission: PermissionName) -> None:
    if not has_permission(user, permission):
        raise PermissionDenied("Usuário sem permissão para esta ação.")


def get_allowed_areas(user):
    if not getattr(user, "is_authenticated", False):
        return []
    areas = list(user.allowed_areas.all())
    if user.area_id and all(area.id != user.area_id for area in areas):
        areas.append(user.area)
    return areas


def has_area_access(user, area) -> bool:
    if area is None:
        return True
    if is_global_user(user):
        return True
    return any(str(allowed_area.id) == str(area.id) for allowed_area in get_allowed_areas(user))


def ensure_area_access(user, area) -> None:
    if not has_area_access(user, area):
        raise PermissionDenied("Usuário sem acesso à área solicitada.")


def can_view_area_data(user) -> bool:
    return has_permission(user, PermissionName.VIEW_AREA_DATA)


def can_manage_area_data(user) -> bool:
    return has_permission(user, PermissionName.MANAGE_AREA_DATA)


def can_manage_team(user) -> bool:
    return get_user_role_name(user) == RoleName.LIDER


def can_view_reports(user) -> bool:
    return has_permission(user, PermissionName.VIEW_REPORTS) or has_permission(
        user,
        PermissionName.VIEW_GLOBAL_REPORTS,
    )


def resolve_area_dashboard_url(area=None) -> str:
    url = reverse("access:area-dashboard")
    if area is None:
        return url
    return f"{url}?area={area.code}"


def resolve_post_login_url(user) -> str:
    areas = [area for area in get_allowed_areas(user) if area]
    preferred_area = getattr(user, "area", None)
    if preferred_area is None and areas:
        preferred_area = areas[0]
    return resolve_area_dashboard_url(preferred_area)
