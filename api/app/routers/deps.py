from __future__ import annotations

from collections.abc import Callable
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import get_db
from app.core.security import decode_access_token
from app.core.enums import RoleName
from app.core.permissions import PermissionName, ensure_any_permission, ensure_permission, get_role_name
from app.db.repositories.users import UserRepository


oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api_v1_prefix}/auth/login")


def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    try:
        payload = decode_access_token(token)
        subject = payload.get("sub")
        if not subject:
            raise ValueError("Missing token subject")
        subject_uuid = UUID(subject)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
        ) from exc

    user = UserRepository(db).get(subject_uuid)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found for token.",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user.",
        )
    return user


def require_roles(*allowed_roles: RoleName) -> Callable:
    def dependency(current_user=Depends(get_current_user)):
        if get_role_name(current_user) not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User does not have enough privileges.",
            )
        return current_user

    return dependency


def require_permission(permission: PermissionName) -> Callable:
    def dependency(current_user=Depends(get_current_user)):
        ensure_permission(current_user, permission)
        return current_user

    return dependency


def require_any_permission(*permissions: PermissionName) -> Callable:
    def dependency(current_user=Depends(get_current_user)):
        ensure_any_permission(current_user, *permissions)
        return current_user

    return dependency

