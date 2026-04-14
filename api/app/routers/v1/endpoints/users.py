from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.routers.deps import require_permission
from app.db.database import get_db
from app.core.permissions import PermissionName
from app.schemas.common import MessageResponse
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.services.users import UserService


router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=list[UserRead])
def list_users(
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(PermissionName.VIEW_USERS)),
):
    return UserService(db).list_users(current_user)


@router.get("/{user_id}", response_model=UserRead)
def get_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(PermissionName.VIEW_USERS)),
):
    return UserService(db).get_user(user_id, current_user)


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(PermissionName.MANAGE_USERS)),
):
    return UserService(db).create_user(payload, current_user)


@router.put("/{user_id}", response_model=UserRead)
def update_user(
    user_id: UUID,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(PermissionName.MANAGE_USERS)),
):
    return UserService(db).update_user(user_id, payload, current_user)


@router.delete("/{user_id}", response_model=MessageResponse)
def delete_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(PermissionName.MANAGE_USERS)),
):
    UserService(db).delete_user(user_id, current_user)
    return MessageResponse(message="User deleted successfully.")

