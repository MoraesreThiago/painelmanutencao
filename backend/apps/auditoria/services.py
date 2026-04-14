from __future__ import annotations

from apps.auditoria.models import AuditLog


def register_audit_event(*, actor_user=None, entity_name: str, entity_id: str, action: str, area=None, summary=None, payload=None):
    return AuditLog.objects.create(
        actor_user=actor_user,
        entity_name=entity_name,
        entity_id=entity_id,
        action=action,
        area=area,
        summary=summary,
        payload=payload,
    )


def audit_logs_for_entity(*, entity_name: str, entity_id: str):
    return AuditLog.objects.select_related("actor_user", "area").filter(
        entity_name=entity_name,
        entity_id=str(entity_id),
    )


def base_audit_queryset():
    return AuditLog.objects.select_related("actor_user", "area").order_by("-created_at")
