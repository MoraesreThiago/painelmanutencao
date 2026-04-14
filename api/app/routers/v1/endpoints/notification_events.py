from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.routers.deps import require_permission
from app.db.database import get_db
from app.core.enums import NotificationStatus
from app.core.notification_events import NotificationEventType
from app.core.permissions import PermissionName
from app.schemas.notification_event import NotificationEventRead
from app.services.notification import NotificationService


router = APIRouter(prefix="/notification-events", tags=["Notification Events"])


@router.get("", response_model=list[NotificationEventRead])
def list_notification_events(
    db: Session = Depends(get_db),
    status_filter: NotificationStatus | None = Query(default=None, alias="status"),
    event_type: NotificationEventType | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    current_user=Depends(require_permission(PermissionName.VIEW_AREA_DATA)),
):
    return NotificationService(db).list_visible(
        current_user,
        status_filter=status_filter,
        event_type=event_type,
        limit=limit,
    )

