from __future__ import annotations

from django.db import models
from django.utils import timezone

from common.enums import NotificationStatus
from common.models import UUIDTimeStampedModel


class NotificationEvent(UUIDTimeStampedModel):
    event_type = models.CharField(max_length=120, db_index=True)
    entity_name = models.CharField(max_length=120, db_index=True)
    entity_id = models.CharField(max_length=80, db_index=True)
    area = models.ForeignKey("unidades.Area", related_name="notification_events", on_delete=models.SET_NULL, blank=True, null=True)
    status = models.CharField(max_length=16, choices=NotificationStatus.choices, default=NotificationStatus.PENDING, db_index=True)
    payload = models.JSONField(blank=True, null=True)
    processing_attempts = models.PositiveIntegerField(default=0)
    occurred_at = models.DateTimeField(default=timezone.now, db_index=True)
    last_attempted_at = models.DateTimeField(blank=True, null=True)
    processed_at = models.DateTimeField(blank=True, null=True)
    last_error = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-occurred_at"]
        verbose_name = "Evento de notificação"
        verbose_name_plural = "Eventos de notificação"
