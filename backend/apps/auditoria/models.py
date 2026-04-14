from __future__ import annotations

from django.db import models

from common.models import UUIDTimeStampedModel


class AuditLog(UUIDTimeStampedModel):
    actor_user = models.ForeignKey(
        "accounts.User",
        related_name="audit_logs",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    entity_name = models.CharField(max_length=120, db_index=True)
    entity_id = models.CharField(max_length=80, db_index=True)
    action = models.CharField(max_length=80, db_index=True)
    area = models.ForeignKey("unidades.Area", related_name="audit_logs", on_delete=models.SET_NULL, blank=True, null=True)
    summary = models.TextField(blank=True, null=True)
    payload = models.JSONField(blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=["entity_name", "entity_id", "created_at"], name="audit_entity_created_idx"),
            models.Index(fields=["area", "created_at"], name="audit_area_created_idx"),
        ]
        ordering = ["-created_at"]
        verbose_name = "Log de auditoria"
        verbose_name_plural = "Logs de auditoria"
