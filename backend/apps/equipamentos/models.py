from __future__ import annotations

from django.db import models

from common.enums import EquipmentStatus, EquipmentType, InstrumentStatus, MotorStatus
from common.models import UUIDTimeStampedModel


class Equipment(UUIDTimeStampedModel):
    code = models.CharField(max_length=80, unique=True, db_index=True)
    tag = models.CharField(max_length=80, unique=True, blank=True, null=True, db_index=True)
    description = models.CharField(max_length=255)
    sector = models.CharField(max_length=120)
    manufacturer = models.CharField(max_length=120, blank=True, null=True)
    model = models.CharField(max_length=120, blank=True, null=True)
    serial_number = models.CharField(max_length=120, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    type = models.CharField(max_length=16, choices=EquipmentType.choices, default=EquipmentType.GENERIC, db_index=True)
    status = models.CharField(max_length=32, choices=EquipmentStatus.choices, default=EquipmentStatus.ACTIVE, db_index=True)
    registered_at = models.DateTimeField()
    area = models.ForeignKey("unidades.Area", related_name="equipments", on_delete=models.CASCADE)
    unidade = models.ForeignKey(
        "unidades.UnidadeProdutiva",
        related_name="equipments",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    location = models.ForeignKey(
        "unidades.Location",
        related_name="equipments",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ["code"]
        verbose_name = "Equipamento"
        verbose_name_plural = "Equipamentos"

    def __str__(self) -> str:
        return f"{self.code} - {self.description}"

    @property
    def resolved_unidade(self):
        if self.unidade_id:
            return self.unidade
        if self.location_id and getattr(self.location, "unidade_id", None):
            return self.location.unidade
        return None

    @property
    def resolved_fabrica(self):
        unidade = self.resolved_unidade
        if unidade is not None:
            return unidade.fabrica
        return None


class Motor(models.Model):
    equipment = models.OneToOneField(
        Equipment,
        related_name="motor",
        on_delete=models.CASCADE,
        primary_key=True,
    )
    electric_motor = models.ForeignKey(
        "motores.ElectricMotor",
        related_name="equipment_motors",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name="Motor elétrico do catálogo",
        help_text="Vínculo com o cadastro técnico em motores.ElectricMotor, quando existir.",
    )
    unique_identifier = models.CharField(max_length=80, unique=True, db_index=True)
    current_status = models.CharField(
        max_length=32,
        choices=MotorStatus.choices,
        default=MotorStatus.IN_OPERATION,
        db_index=True,
    )
    last_internal_service_at = models.DateField(blank=True, null=True)

    class Meta:
        ordering = ["unique_identifier"]
        verbose_name = "Motor"
        verbose_name_plural = "Motores"

    def __str__(self) -> str:
        return self.unique_identifier

    @property
    def burned_cases(self):
        """Processos de motor queimado associados via catálogo elétrico."""
        if self.electric_motor_id:
            return self.electric_motor.burned_cases.all()
        from apps.motores.models import BurnedMotorCase

        return BurnedMotorCase.objects.none()


class Instrument(models.Model):
    equipment = models.OneToOneField(
        Equipment,
        related_name="instrument",
        on_delete=models.CASCADE,
        primary_key=True,
    )
    unique_identifier = models.CharField(max_length=80, unique=True, db_index=True)
    instrument_type = models.CharField(max_length=120)
    current_status = models.CharField(
        max_length=32,
        choices=InstrumentStatus.choices,
        default=InstrumentStatus.IN_STOCK,
        db_index=True,
    )
    calibration_due_date = models.DateField(blank=True, null=True)

    class Meta:
        ordering = ["unique_identifier"]
        verbose_name = "Instrumento"
        verbose_name_plural = "Instrumentos"

    def __str__(self) -> str:
        return self.unique_identifier
