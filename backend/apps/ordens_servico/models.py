from __future__ import annotations

from django.db import models
from django.utils import timezone

from common.enums import ExternalServiceStatus
from common.models import UUIDTimeStampedModel


class ExternalServiceOrder(UUIDTimeStampedModel):
    motor = models.ForeignKey("equipamentos.Motor", related_name="external_service_orders", on_delete=models.CASCADE)
    sent_at = models.DateTimeField(default=timezone.now, db_index=True)
    reason = models.CharField(max_length=255)
    vendor_name = models.CharField(max_length=160)
    work_order_number = models.CharField(max_length=80, db_index=True)
    authorized_by_user = models.ForeignKey(
        "accounts.User",
        related_name="authorized_service_orders",
        on_delete=models.CASCADE,
    )
    registered_by_user = models.ForeignKey(
        "accounts.User",
        related_name="registered_service_orders",
        on_delete=models.CASCADE,
    )
    expected_return_at = models.DateTimeField(blank=True, null=True)
    actual_return_at = models.DateTimeField(blank=True, null=True)
    service_status = models.CharField(
        max_length=32,
        choices=ExternalServiceStatus.choices,
        default=ExternalServiceStatus.OPEN,
        db_index=True,
    )
    notes = models.TextField(blank=True, null=True)
    attachments_metadata = models.JSONField(blank=True, null=True)

    class Meta:
        ordering = ["-sent_at"]
        verbose_name = "Ordem de serviço externa"
        verbose_name_plural = "Ordens de serviço externas"
