from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.routers.deps import require_permission
from app.db.database import get_db
from app.core.permissions import PermissionName
from app.schemas.collaborator import CollaboratorCreate, CollaboratorRead, CollaboratorUpdate
from app.schemas.common import MessageResponse
from app.services.collaborators import CollaboratorService


router = APIRouter(prefix="/collaborators", tags=["Collaborators"])


@router.get("", response_model=list[CollaboratorRead])
def list_collaborators(
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(PermissionName.MANAGE_AREA_DATA)),
):
    return CollaboratorService(db).list_collaborators(current_user)


@router.get("/{collaborator_id}", response_model=CollaboratorRead)
def get_collaborator(
    collaborator_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(PermissionName.MANAGE_AREA_DATA)),
):
    return CollaboratorService(db).get_collaborator(collaborator_id, current_user)


@router.post("", response_model=CollaboratorRead, status_code=status.HTTP_201_CREATED)
def create_collaborator(
    payload: CollaboratorCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(PermissionName.MANAGE_AREA_DATA)),
):
    return CollaboratorService(db).create_collaborator(payload, current_user)


@router.put("/{collaborator_id}", response_model=CollaboratorRead)
def update_collaborator(
    collaborator_id: UUID,
    payload: CollaboratorUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(PermissionName.MANAGE_AREA_DATA)),
):
    return CollaboratorService(db).update_collaborator(collaborator_id, payload, current_user)


@router.delete("/{collaborator_id}", response_model=MessageResponse)
def delete_collaborator(
    collaborator_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(PermissionName.MANAGE_USERS)),
):
    CollaboratorService(db).delete_collaborator(collaborator_id, current_user)
    return MessageResponse(message="Collaborator deleted successfully.")

