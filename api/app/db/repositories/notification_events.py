from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select

from app.core.notification_events import NotificationEventType
from app.core.enums import NotificationStatus
from app.core.permissions import apply_area_scope
from app.models.notification_event import NotificationEvent
from app.models.user import User
from app.db.repositories.base import BaseRepository


class NotificationEventRepository(BaseRepository[NotificationEvent]):
    model = NotificationEvent

    def list_visible(
        self,
        current_user: User,
        *,
        status_filter: NotificationStatus | None = None,
        event_type: str | NotificationEventType | None = None,
        limit: int = 100,
    ) -> list[NotificationEvent]:
        stmt = (
            apply_area_scope(select(NotificationEvent), current_user, NotificationEvent)
            .order_by(NotificationEvent.occurred_at.desc())
        )
        if status_filter is not None:
            stmt = stmt.where(NotificationEvent.status == status_filter)
        if event_type:
            normalized_event_type = (
                event_type.value if isinstance(event_type, NotificationEventType) else str(event_type)
            )
            stmt = stmt.where(NotificationEvent.event_type == normalized_event_type)
        return self.list(statement=stmt, limit=limit)

    def list_pending(self, *, limit: int = 100) -> list[NotificationEvent]:
        stmt = (
            select(NotificationEvent)
            .where(NotificationEvent.status == NotificationStatus.PENDING)
            .order_by(NotificationEvent.occurred_at.asc())
        )
        return self.list(statement=stmt, limit=limit)

    def mark_processed(
        self,
        event: NotificationEvent,
        *,
        processed_at: datetime | None = None,
    ) -> NotificationEvent:
        timestamp = processed_at or datetime.now(UTC)
        event.status = NotificationStatus.PROCESSED
        event.last_attempted_at = timestamp
        event.processed_at = timestamp
        event.last_error = None
        event.processing_attempts += 1
        self.db.add(event)
        self.db.flush()
        return event

    def mark_error(self, event: NotificationEvent, *, error_message: str) -> NotificationEvent:
        event.status = NotificationStatus.ERROR
        event.last_attempted_at = datetime.now(UTC)
        event.processed_at = None
        event.last_error = error_message
        event.processing_attempts += 1
        self.db.add(event)
        self.db.flush()
        return event

    def requeue(self, event: NotificationEvent) -> NotificationEvent:
        event.status = NotificationStatus.PENDING
        event.processed_at = None
        event.last_error = None
        self.db.add(event)
        self.db.flush()
        return event

