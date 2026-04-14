from __future__ import annotations

from django.db import models

from common.enums import RoleName
from common.models import UUIDTimeStampedModel


class Role(UUIDTimeStampedModel):
    name = models.CharField(max_length=32, choices=RoleName.choices, unique=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Papel"
        verbose_name_plural = "Papéis"

    def __str__(self) -> str:
        return self.get_name_display()


class UserArea(UUIDTimeStampedModel):
    user = models.ForeignKey("accounts.User", related_name="area_assignments", on_delete=models.CASCADE)
    area = models.ForeignKey("unidades.Area", related_name="user_area_assignments", on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "area"], name="uq_user_area_user_area"),
        ]
        verbose_name = "Vinculação usuário-área"
        verbose_name_plural = "Vinculações usuário-área"

    def __str__(self) -> str:
        return f"{self.user} - {self.area}"
