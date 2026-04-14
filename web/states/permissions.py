from __future__ import annotations


ROLE_LEVELS = {
    "MANUTENTOR": 1,
    "INSPETOR": 2,
    "LIDER": 2,
    "SUPERVISOR": 3,
    "GERENTE": 4,
    "ADMIN": 5,
}


def role_level(role_name: str | None) -> int:
    if not role_name:
        return 0
    return ROLE_LEVELS.get(role_name, 0)


def has_permission(permissions: list[str], permission: str | None) -> bool:
    if permission is None:
        return True
    return permission in permissions


def can_manage_collaborators(role_name: str | None, permissions: list[str]) -> bool:
    return role_level(role_name) >= 2 and "manage_area_data" in permissions

