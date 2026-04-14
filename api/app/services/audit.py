from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.user import User
from app.utils.serialization import to_serializable


class AuditService:
    def __init__(self, db: Session):
        self.db = db

    def record(
        self,
        *,
        actor: User | None,
        entity_name: str,
        entity_id: str,
        action: str,
        area_id=None,
        summary: str | None = None,
        payload: dict | None = None,
    ) -> AuditLog:
        entry = AuditLog(
            actor_user_id=getattr(actor, "id", None),
            entity_name=entity_name,
            entity_id=entity_id,
            action=action,
            area_id=area_id,
            summary=summary,
            payload=to_serializable(payload) if payload else None,
        )
        self.db.add(entry)
        self.db.flush()
        return entry

