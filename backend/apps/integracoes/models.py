from __future__ import annotations

from django.db import models
from django.utils import timezone

from common.models import UUIDTimeStampedModel


class SyncOutboxEntry(UUIDTimeStampedModel):
    source = models.CharField(max_length=80, default="pwa")
    entity_name = models.CharField(max_length=120, db_index=True)
    entity_id = models.CharField(max_length=80, blank=True, null=True, db_index=True)
    action = models.CharField(max_length=40)
    payload = models.JSONField()
    synced_at = models.DateTimeField(blank=True, null=True)
    failed_at = models.DateTimeField(blank=True, null=True)
    last_error = models.TextField(blank=True, null=True)
    received_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["-received_at"]
        verbose_name = "Item de sincronização"
        verbose_name_plural = "Itens de sincronização"
