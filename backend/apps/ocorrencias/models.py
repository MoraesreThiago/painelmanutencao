from __future__ import annotations

from django.db import models
from django.utils import timezone

from common.enums import (
    BurnedMotorStatus,
    InstrumentServiceStatus,
    InstrumentServiceType,
    OccurrenceClassification,
    OccurrenceStatus,
)
from common.models import UUIDTimeStampedModel


class Occurrence(UUIDTimeStampedModel):
    equipment = models.ForeignKey(
        "equipamentos.Equipment",
        related_name="occurrences",
        on_delete=models.PROTECT,
    )
    area = models.ForeignKey(
        "unidades.Area",
        related_name="occurrences",
        on_delete=models.PROTECT,
    )
    location = models.ForeignKey(
        "unidades.Location",
        related_name="occurrences",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    unidade = models.ForeignKey(
        "unidades.UnidadeProdutiva",
        related_name="occurrences",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    responsible_collaborator = models.ForeignKey(
        "colaboradores.Collaborator",
        related_name="occurrences",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    reported_by_user = models.ForeignKey(
        "accounts.User",
        related_name="reported_occurrences",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    classification = models.CharField(
        max_length=32,
        choices=OccurrenceClassification.choices,
        default=OccurrenceClassification.FAILURE,
        db_index=True,
    )
    status = models.CharField(
        max_length=32,
        choices=OccurrenceStatus.choices,
        default=OccurrenceStatus.OPEN,
        db_index=True,
    )
    occurred_at = models.DateTimeField(default=timezone.now, db_index=True)
    resolved_at = models.DateTimeField(blank=True, null=True)
    description = models.TextField()
    notes = models.TextField(blank=True, null=True)
    had_downtime = models.BooleanField(default=False, db_index=True)
    downtime_minutes = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(had_downtime=False, downtime_minutes__isnull=True)
                    | models.Q(had_downtime=True, downtime_minutes__isnull=False)
                ),
                name="occurrence_downtime_consistency",
            ),
        ]
        indexes = [
            models.Index(fields=["area", "status", "occurred_at"], name="occ_area_status_occurred_idx"),
            models.Index(fields=["equipment", "occurred_at"], name="occ_equipment_occurred_idx"),
            models.Index(fields=["classification", "occurred_at"], name="occ_class_occurred_idx"),
        ]
        ordering = ["-occurred_at", "-created_at"]
        verbose_name = "Ocorrencia"
        verbose_name_plural = "Ocorrencias"

    def __str__(self) -> str:
        return f"{self.equipment.code} - {self.get_status_display()}"

    @property
    def resolved_unidade(self):
        if self.unidade_id:
            return self.unidade
        if self.location_id and getattr(self.location, "unidade_id", None):
            return self.location.unidade
        return self.equipment.resolved_unidade

    @property
    def resolved_fabrica(self):
        unidade = self.resolved_unidade
        if unidade is not None:
            return unidade.fabrica
        return None


class Movement(UUIDTimeStampedModel):
    equipment = models.ForeignKey("equipamentos.Equipment", related_name="movements", on_delete=models.CASCADE)
    previous_location = models.ForeignKey(
        "unidades.Location",
        related_name="previous_movements",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    new_location = models.ForeignKey(
        "unidades.Location",
        related_name="new_movements",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    moved_by_user = models.ForeignKey("accounts.User", related_name="movements", on_delete=models.CASCADE)
    moved_at = models.DateTimeField(default=timezone.now, db_index=True)
    reason = models.CharField(max_length=255)
    status_after = models.CharField(max_length=80, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-moved_at"]
        verbose_name = "Movimentacao"
        verbose_name_plural = "Movimentacoes"


class BurnedMotorRecord(UUIDTimeStampedModel):
    area = models.ForeignKey("unidades.Area", related_name="burned_motor_records", on_delete=models.CASCADE)
    motor = models.ForeignKey("equipamentos.Motor", related_name="burned_motor_records", on_delete=models.CASCADE)
    source_equipment_tag = models.CharField(max_length=80, db_index=True)
    recorded_at = models.DateTimeField(default=timezone.now, db_index=True)
    diagnosis = models.CharField(max_length=255)
    status = models.CharField(max_length=32, choices=BurnedMotorStatus.choices, default=BurnedMotorStatus.OPEN)
    notes = models.TextField(blank=True, null=True)
    recorded_by_user = models.ForeignKey(
        "accounts.User",
        related_name="burned_motor_records",
        on_delete=models.CASCADE,
    )

    class Meta:
        ordering = ["-recorded_at"]
        verbose_name = "Registro de motor queimado"
        verbose_name_plural = "Registros de motores queimados"


class InstrumentServiceRequest(UUIDTimeStampedModel):
    area = models.ForeignKey("unidades.Area", related_name="instrument_service_requests", on_delete=models.CASCADE)
    instrument = models.ForeignKey("equipamentos.Instrument", related_name="service_requests", on_delete=models.CASCADE)
    service_type = models.CharField(max_length=32, choices=InstrumentServiceType.choices)
    service_status = models.CharField(
        max_length=32,
        choices=InstrumentServiceStatus.choices,
        default=InstrumentServiceStatus.OPEN,
    )
    requested_at = models.DateTimeField(default=timezone.now, db_index=True)
    expected_return_at = models.DateTimeField(blank=True, null=True)
    actual_return_at = models.DateTimeField(blank=True, null=True)
    vendor_name = models.CharField(max_length=160, blank=True, null=True)
    vendor_reference = models.CharField(max_length=80, blank=True, null=True)
    reason = models.CharField(max_length=255)
    notes = models.TextField(blank=True, null=True)
    registered_by_user = models.ForeignKey(
        "accounts.User",
        related_name="instrument_service_requests",
        on_delete=models.CASCADE,
    )

    class Meta:
        ordering = ["-requested_at"]
        verbose_name = "Solicitacao de servico de instrumento"
        verbose_name_plural = "Solicitacoes de servico de instrumentos"
