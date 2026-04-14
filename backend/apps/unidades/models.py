from __future__ import annotations

from django.db import models

from common.enums import AreaCode
from common.models import UUIDTimeStampedModel


class Area(UUIDTimeStampedModel):
    name = models.CharField(max_length=120, unique=True)
    code = models.CharField(max_length=32, choices=AreaCode.choices, unique=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Area"
        verbose_name_plural = "Areas"

    def __str__(self) -> str:
        return self.name


class Fabrica(UUIDTimeStampedModel):
    name = models.CharField(max_length=120, unique=True)
    code = models.CharField(max_length=32, unique=True, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Fabrica"
        verbose_name_plural = "Fabricas"

    def __str__(self) -> str:
        return self.name


class UnidadeProdutiva(UUIDTimeStampedModel):
    fabrica = models.ForeignKey("unidades.Fabrica", related_name="unidades_produtivas", on_delete=models.CASCADE)
    name = models.CharField(max_length=120)
    code = models.CharField(max_length=32)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["fabrica__name", "name"]
        verbose_name = "Unidade produtiva"
        verbose_name_plural = "Unidades produtivas"
        constraints = [
            models.UniqueConstraint(fields=["fabrica", "code"], name="uq_unidade_produtiva_fabrica_code"),
        ]

    def __str__(self) -> str:
        return f"{self.fabrica.name} - {self.name}"


class Location(UUIDTimeStampedModel):
    name = models.CharField(max_length=120)
    sector = models.CharField(max_length=120)
    description = models.TextField(blank=True, null=True)
    area = models.ForeignKey(Area, related_name="locations", on_delete=models.CASCADE)
    unidade = models.ForeignKey(
        "unidades.UnidadeProdutiva",
        related_name="locations",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["name", "sector", "area", "unidade"],
                name="uq_location_name_sector_area_unidade",
            ),
        ]
        ordering = ["area__name", "unidade__fabrica__name", "unidade__name", "sector", "name"]
        verbose_name = "Localizacao"
        verbose_name_plural = "Localizacoes"

    @property
    def fabrica(self):
        if self.unidade_id:
            return self.unidade.fabrica
        return None

    def __str__(self) -> str:
        if self.unidade_id:
            return f"{self.unidade.name} - {self.name} ({self.sector})"
        return f"{self.name} ({self.sector})"
