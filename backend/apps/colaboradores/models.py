from __future__ import annotations

from django.db import models

from common.enums import RecordStatus
from common.models import UUIDTimeStampedModel


class Collaborator(UUIDTimeStampedModel):
    full_name = models.CharField(max_length=255)
    registration_number = models.CharField(max_length=80, unique=True)
    job_title = models.CharField(max_length=120)
    contact_phone = models.CharField(max_length=40, blank=True, null=True)
    status = models.CharField(max_length=16, choices=RecordStatus.choices, default=RecordStatus.ACTIVE)
    area = models.ForeignKey("unidades.Area", related_name="collaborators", on_delete=models.CASCADE)
    linked_user = models.OneToOneField(
        "accounts.User",
        related_name="collaborator",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ["full_name"]
        verbose_name = "Colaborador"
        verbose_name_plural = "Colaboradores"

    def __str__(self) -> str:
        return self.full_name
