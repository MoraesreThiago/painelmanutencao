from __future__ import annotations

from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.enums import NotificationStatus
from app.core.notification_events import NotificationEventType
from app.core.permissions import PermissionName, ensure_permission
from app.models.notification_event import NotificationEvent
from app.db.repositories.notification_events import NotificationEventRepository
from app.utils.serialization import to_serializable


class NotificationService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = NotificationEventRepository(db)

    def list_visible(
        self,
        current_user,
        *,
        status_filter: NotificationStatus | None = None,
        event_type: str | NotificationEventType | None = None,
        limit: int = 100,
    ) -> list[NotificationEvent]:
        ensure_permission(current_user, PermissionName.VIEW_AREA_DATA)
        return self.repository.list_visible(
            current_user,
            status_filter=status_filter,
            event_type=event_type,
            limit=limit,
        )

    def enqueue(
        self,
        *,
        event_type: str | NotificationEventType,
        entity_name: str,
        entity_id: str,
        area_id=None,
        payload: dict | None = None,
    ) -> NotificationEvent:
        normalized_event_type = (
            event_type.value if isinstance(event_type, NotificationEventType) else str(event_type)
        )
        event = self.repository.create(
            {
                "event_type": normalized_event_type,
                "entity_name": entity_name,
                "entity_id": entity_id,
                "area_id": area_id,
                "payload": to_serializable(payload) if payload else None,
            },
        )
        return event


class NotificationDispatchService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = NotificationEventRepository(db)

    def list_pending(self, *, limit: int = 100) -> list[NotificationEvent]:
        return self.repository.list_pending(limit=limit)

    def get_event(self, event_id) -> NotificationEvent:
        event = self.repository.get(event_id)
        if event is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification event not found.",
            )
        return event

    @staticmethod
    def _ensure_transition(
        event: NotificationEvent,
        *,
        allowed_statuses: set[NotificationStatus],
        target_status: NotificationStatus,
    ) -> None:
        if event.status in allowed_statuses:
            return
        allowed_names = ", ".join(status.value for status in sorted(allowed_statuses, key=lambda item: item.value))
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Notification event cannot transition from {event.status.value} to "
                f"{target_status.value}. Allowed source states: {allowed_names}."
            ),
        )

    def mark_processed(self, event_id, *, processed_at: datetime | None = None) -> NotificationEvent:
        event = self.get_event(event_id)
        self._ensure_transition(
            event,
            allowed_statuses={NotificationStatus.PENDING},
            target_status=NotificationStatus.PROCESSED,
        )
        return self.repository.mark_processed(event, processed_at=processed_at or datetime.now(UTC))

    def mark_error(self, event_id, *, error_message: str) -> NotificationEvent:
        event = self.get_event(event_id)
        self._ensure_transition(
            event,
            allowed_statuses={NotificationStatus.PENDING},
            target_status=NotificationStatus.ERROR,
        )
        return self.repository.mark_error(event, error_message=error_message)

    def requeue(self, event_id) -> NotificationEvent:
        event = self.get_event(event_id)
        self._ensure_transition(
            event,
            allowed_statuses={NotificationStatus.ERROR},
            target_status=NotificationStatus.PENDING,
        )
        return self.repository.requeue(event)

