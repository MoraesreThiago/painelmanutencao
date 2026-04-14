from __future__ import annotations

from uuid import uuid4

from app.core.enums import RoleName
from app.core.permissions import (
    PermissionName,
    can_manage_users,
    get_user_permissions,
    has_area_access,
    is_global_user,
)
from app.models.role import Role
from app.models.user import User
from app.models.user_area import UserArea


def build_user(role_name: RoleName, *, area_ids: list | None = None) -> User:
    user = User(
        full_name=f"User {role_name.value}",
        email=f"{role_name.value.lower()}@example.com",
        password_hash="hashed",
        role=Role(name=role_name),
        role_id=uuid4(),
    )
    for area_id in area_ids or []:
        user.area_assignments.append(UserArea(area_id=area_id))
    return user


def test_permission_hierarchy_is_incremental() -> None:
    manutentor = build_user(RoleName.MANUTENTOR)
    supervisor = build_user(RoleName.SUPERVISOR)
    admin = build_user(RoleName.ADMIN)

    manutentor_permissions = get_user_permissions(manutentor)
    supervisor_permissions = get_user_permissions(supervisor)
    admin_permissions = get_user_permissions(admin)

    assert PermissionName.VIEW_AREA_DATA in manutentor_permissions
    assert PermissionName.CREATE_OCCURRENCES in manutentor_permissions
    assert PermissionName.MANAGE_USERS not in manutentor_permissions
    assert PermissionName.MANAGE_AREA_DATA not in manutentor_permissions

    assert PermissionName.VIEW_USERS in supervisor_permissions
    assert PermissionName.DELETE_AREA_DATA in supervisor_permissions
    assert PermissionName.MANAGE_USERS not in supervisor_permissions

    assert PermissionName.MANAGE_USERS in admin_permissions
    assert PermissionName.ASSUME_AREA_CONTEXT in admin_permissions
    assert can_manage_users(admin) is True


def test_area_access_supports_multiple_areas() -> None:
    area_a = uuid4()
    area_b = uuid4()
    outsider_area = uuid4()

    supervisor = build_user(RoleName.SUPERVISOR, area_ids=[area_a, area_b])
    gerente = build_user(RoleName.GERENTE)

    assert has_area_access(supervisor, area_a) is True
    assert has_area_access(supervisor, area_b) is True
    assert has_area_access(supervisor, outsider_area) is False

    assert is_global_user(gerente) is True
    assert has_area_access(gerente, outsider_area) is True

