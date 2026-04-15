from __future__ import annotations

from django.db import models
from django.utils import timezone

from common.enums import (
    AreaCode,
    BurnedMotorCaseStatus,
    BurnedMotorPriority,
    MotorBurnoutFlowStatus,
    MotorDataOrigin,
    MotorSolutionType,
    MotorStatus,
)
from common.models import UUIDTimeStampedModel


class ElectricMotor(UUIDTimeStampedModel):
    area = models.ForeignKey("unidades.Area", related_name="electric_motors", on_delete=models.CASCADE)
    unidade = models.ForeignKey(
        "unidades.UnidadeProdutiva",
        related_name="electric_motors",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    mo = models.CharField(max_length=80, unique=True, db_index=True, verbose_name="MO")
    description = models.CharField(max_length=160, blank=True, null=True, verbose_name="Descricao do motor")
    power = models.CharField(max_length=80, verbose_name="Potencia")
    manufacturer = models.CharField(max_length=120, verbose_name="Fabricante")
    frame = models.CharField(max_length=80, verbose_name="Carcaca")
    rpm = models.PositiveIntegerField(verbose_name="RPM")
    voltage = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Tensao")
    current = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Corrente")
    location_name = models.CharField(max_length=160, blank=True, null=True, verbose_name="Local / setor")
    is_provisional = models.BooleanField(default=False, db_index=True, verbose_name="Cadastro provisório")
    notes = models.TextField(blank=True, null=True, verbose_name="Observacao")
    status = models.CharField(
        max_length=32,
        choices=MotorStatus.choices,
        default=MotorStatus.IN_OPERATION,
        db_index=True,
        verbose_name="Status",
    )
    registered_at = models.DateTimeField(default=timezone.now, db_index=True, verbose_name="Data de cadastro")
    registered_by_user = models.ForeignKey(
        "accounts.User",
        related_name="registered_electric_motors",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name="Responsavel pelo cadastro",
    )

    class Meta:
        ordering = ["mo"]
        indexes = [
            models.Index(fields=["area", "status"], name="motor_area_status_idx"),
            models.Index(fields=["manufacturer", "frame"], name="motor_maker_frame_idx"),
        ]
        verbose_name = "Motor eletrico"
        verbose_name_plural = "Motores eletricos"

    def __str__(self) -> str:
        return self.mo

    @property
    def is_electrical_area(self) -> bool:
        return self.area.code == AreaCode.ELETRICA

    @property
    def resolved_fabrica(self):
        if self.unidade_id:
            return self.unidade.fabrica
        return None


# DEPRECIADO — não usar em código novo. Use BurnedMotorCase.
# Mantido apenas para preservar dados históricos até migração definitiva.
class BurnedMotorProcess(UUIDTimeStampedModel):
    motor = models.ForeignKey("motores.ElectricMotor", related_name="burned_processes", on_delete=models.CASCADE)
    occurred_at = models.DateTimeField(default=timezone.now, db_index=True, verbose_name="Data da ocorrencia")
    problem_type = models.CharField(max_length=120, verbose_name="Tipo do problema")
    description = models.TextField(verbose_name="Descricao")
    sent_to_pcm = models.BooleanField(default=False, db_index=True, verbose_name="Enviado para PCM")
    sent_to_pcm_at = models.DateTimeField(blank=True, null=True, verbose_name="Data de envio para PCM")
    in_quotation = models.BooleanField(default=False, db_index=True, verbose_name="Em cotacao")
    payment_approved = models.BooleanField(default=False, db_index=True, verbose_name="Pagamento aprovado")
    approved_at = models.DateTimeField(blank=True, null=True, verbose_name="Data de aprovacao")
    arrived = models.BooleanField(default=False, db_index=True, verbose_name="Chegou")
    arrived_at = models.DateTimeField(blank=True, null=True, verbose_name="Data de chegada")
    sent_for_rewinding = models.BooleanField(default=False, verbose_name="Foi para rebobinamento")
    third_party_company = models.CharField(
        max_length=160,
        blank=True,
        null=True,
        verbose_name="Empresa terceira",
    )
    notes = models.TextField(blank=True, null=True, verbose_name="Observacoes")
    status = models.CharField(
        max_length=32,
        choices=MotorBurnoutFlowStatus.choices,
        default=MotorBurnoutFlowStatus.REGISTERED,
        db_index=True,
        verbose_name="Status atual",
    )
    registered_by_user = models.ForeignKey(
        "accounts.User",
        related_name="registered_motor_burnout_processes",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name="Registrado por",
    )
    updated_by_user = models.ForeignKey(
        "accounts.User",
        related_name="updated_motor_burnout_processes",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name="Atualizado por",
    )

    class Meta:
        ordering = ["-occurred_at", "-created_at"]
        indexes = [
            models.Index(fields=["motor", "status"], name="burn_motor_status_idx"),
            models.Index(fields=["occurred_at"], name="burn_occurred_idx"),
        ]
        verbose_name = "Fluxo de motor queimado"
        verbose_name_plural = "Fluxos de motores queimados"

    def __str__(self) -> str:
        return f"{self.motor.mo} - {self.get_status_display()}"


class BurnedMotorCase(UUIDTimeStampedModel):
    area = models.ForeignKey("unidades.Area", related_name="burned_motor_cases", on_delete=models.CASCADE)
    unidade = models.ForeignKey(
        "unidades.UnidadeProdutiva",
        related_name="burned_motor_cases",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name="Unidade produtiva",
    )
    process_code = models.CharField(max_length=32, unique=True, blank=True, db_index=True, verbose_name="Codigo do processo")
    motor = models.ForeignKey(
        "motores.ElectricMotor",
        related_name="burned_cases",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name="Motor relacionado",
    )
    data_origin = models.CharField(
        max_length=24,
        choices=MotorDataOrigin.choices,
        default=MotorDataOrigin.MANUAL,
        db_index=True,
        verbose_name="Origem dos dados do motor",
    )
    motor_description = models.CharField(max_length=160, blank=True, verbose_name="Descricao do motor")
    motor_mo = models.CharField(max_length=80, blank=True, verbose_name="MO")
    motor_power = models.CharField(max_length=80, blank=True, verbose_name="Potencia")
    motor_manufacturer = models.CharField(max_length=120, blank=True, verbose_name="Fabricante")
    motor_frame = models.CharField(max_length=80, blank=True, verbose_name="Carcaca")
    motor_rpm = models.PositiveIntegerField(blank=True, null=True, verbose_name="RPM")
    motor_voltage = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Tensao")
    motor_current = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Corrente")
    motor_location = models.CharField(max_length=160, blank=True, verbose_name="Local / setor")
    occurred_at = models.DateTimeField(default=timezone.now, db_index=True, verbose_name="Data da ocorrencia")
    recorded_at = models.DateTimeField(default=timezone.now, db_index=True, verbose_name="Data do registro")
    requester_name = models.CharField(max_length=255, verbose_name="Solicitante")
    problem_type = models.CharField(max_length=120, verbose_name="Tipo do problema")
    defect_description = models.TextField(verbose_name="Descricao do defeito")
    technical_notes = models.TextField(blank=True, verbose_name="Observacoes tecnicas")
    priority = models.CharField(
        max_length=24,
        choices=BurnedMotorPriority.choices,
        default=BurnedMotorPriority.MEDIUM,
        db_index=True,
        verbose_name="Prioridade",
    )
    needs_pcm = models.BooleanField(default=True, verbose_name="Precisa enviar ao PCM")
    sent_to_pcm = models.BooleanField(default=False, db_index=True, verbose_name="Enviado ao PCM")
    sent_to_pcm_at = models.DateTimeField(blank=True, null=True, verbose_name="Data de envio ao PCM")
    pcm_responsible = models.CharField(max_length=140, blank=True, verbose_name="PCM responsavel")
    sent_to_finance = models.BooleanField(default=False, db_index=True, verbose_name="Enviado ao financeiro")
    finance_sent_at = models.DateTimeField(blank=True, null=True, verbose_name="Data de envio ao financeiro")
    approved = models.BooleanField(default=False, db_index=True, verbose_name="Pedido aprovado")
    approved_at = models.DateTimeField(blank=True, null=True, verbose_name="Data da aprovacao")
    solution_type = models.CharField(
        max_length=32,
        choices=MotorSolutionType.choices,
        default=MotorSolutionType.UNDER_EVALUATION,
        verbose_name="Tipo de solucao",
    )
    purchase_new_motor = models.BooleanField(default=False, verbose_name="Compra de motor novo")
    rewinding_required = models.BooleanField(default=False, verbose_name="Precisa rebobinamento")
    third_party_company = models.CharField(max_length=160, blank=True, verbose_name="Empresa terceira")
    third_party_contact = models.CharField(max_length=160, blank=True, verbose_name="Contato da empresa")
    freight_requested = models.BooleanField(default=False, db_index=True, verbose_name="Frete/coleta solicitado")
    pickup_at = models.DateTimeField(blank=True, null=True, verbose_name="Data da coleta")
    expected_return_at = models.DateTimeField(blank=True, null=True, verbose_name="Data prevista de retorno")
    arrived_at = models.DateTimeField(blank=True, null=True, verbose_name="Data de chegada")
    progress_notes = models.TextField(blank=True, verbose_name="Observacoes do andamento")
    status = models.CharField(
        max_length=40,
        choices=BurnedMotorCaseStatus.choices,
        default=BurnedMotorCaseStatus.OPEN,
        db_index=True,
        verbose_name="Status atual",
    )
    pcm_email_sent = models.BooleanField(default=False, db_index=True, verbose_name="E-mail enviado ao PCM")
    pcm_email_sent_at = models.DateTimeField(blank=True, null=True, verbose_name="Data de envio do e-mail ao PCM")
    opened_by_user = models.ForeignKey(
        "accounts.User",
        related_name="opened_burned_motor_cases",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name="Responsavel pela abertura",
    )
    updated_by_user = models.ForeignKey(
        "accounts.User",
        related_name="updated_burned_motor_cases",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name="Ultima atualizacao por",
    )

    class Meta:
        ordering = ["-occurred_at", "-updated_at"]
        indexes = [
            models.Index(fields=["area", "status"], name="burned_case_area_status_idx"),
            models.Index(fields=["process_code"], name="burned_case_code_idx"),
            models.Index(fields=["expected_return_at"], name="burned_case_return_idx"),
        ]
        verbose_name = "Processo de motor queimado"
        verbose_name_plural = "Processos de motores queimados"

    def __str__(self) -> str:
        return self.process_code or f"Processo {self.id}"

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new and not self.process_code:
            code = f"MQ-{self.created_at:%Y%m%d}-{str(self.id).split('-')[0].upper()}"
            type(self).objects.filter(pk=self.pk).update(process_code=code)
            self.process_code = code

    @property
    def display_motor_label(self) -> str:
        return self.motor_description or self.motor_mo or "Motor nao identificado"

    @property
    def is_overdue(self) -> bool:
        final_statuses = {
            BurnedMotorCaseStatus.RECEIVED,
            BurnedMotorCaseStatus.COMPLETED,
            BurnedMotorCaseStatus.CANCELLED,
        }
        return bool(
            self.expected_return_at
            and self.expected_return_at < timezone.now()
            and self.status not in final_statuses
        )

    @property
    def resolved_unidade(self):
        if self.unidade_id:
            return self.unidade
        if self.motor_id and self.motor.unidade_id:
            return self.motor.unidade
        return None

    @property
    def resolved_fabrica(self):
        unidade = self.resolved_unidade
        if unidade is not None:
            return unidade.fabrica
        return None


class BurnedMotorCaseEvent(UUIDTimeStampedModel):
    case = models.ForeignKey("motores.BurnedMotorCase", related_name="events", on_delete=models.CASCADE)
    actor_user = models.ForeignKey(
        "accounts.User",
        related_name="burned_motor_case_events",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name="Usuario responsavel",
    )
    event_type = models.CharField(max_length=32, default="note", verbose_name="Tipo do evento")
    title = models.CharField(max_length=160, verbose_name="Titulo")
    details = models.TextField(blank=True, verbose_name="Detalhes")
    event_at = models.DateTimeField(default=timezone.now, db_index=True, verbose_name="Data do evento")

    class Meta:
        ordering = ["-event_at", "-created_at"]
        indexes = [
            models.Index(fields=["case", "event_at"], name="burned_case_event_idx"),
        ]
        verbose_name = "Evento do processo de motor queimado"
        verbose_name_plural = "Eventos do processo de motor queimado"

    def __str__(self) -> str:
        return f"{self.case.process_code} - {self.title}"
