from __future__ import annotations

from django import forms
from django.db.models import Q
from django.utils import timezone

from apps.motores.models import BurnedMotorCase, BurnedMotorProcess, ElectricMotor
from apps.motores.services import validate_burned_case_form_data
from apps.unidades.models import UnidadeProdutiva
from apps.unidades.services import get_fabricas_visiveis, get_unidades_visiveis
from common.enums import (
    BurnedMotorCaseStatus,
    BurnedMotorPriority,
    MotorBurnoutFlowStatus,
    MotorSolutionType,
    MotorStatus,
)


PROCESS_STAGE_CHOICES = [
    ("", "Todas as etapas"),
    ("pcm", "PCM"),
    ("financeiro", "Financeiro"),
    ("terceiro", "Empresa terceira"),
    ("frete", "Frete / coleta"),
    ("retorno", "Retorno"),
]


class UnidadeProdutivaChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return f"{obj.fabrica.name} - {obj.name}"


class MotorCatalogChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        parts = [obj.mo]
        if obj.description:
            parts.append(obj.description)
        if obj.unidade_id:
            parts.append(f"{obj.unidade.fabrica.name} - {obj.unidade.name}")
        if obj.location_name:
            parts.append(obj.location_name)
        parts.extend([str(obj.power), obj.manufacturer])
        return " | ".join(str(part) for part in parts if part)


class ElectricMotorForm(forms.ModelForm):
    unidade = UnidadeProdutivaChoiceField(
        queryset=UnidadeProdutiva.objects.none(),
        required=False,
        label="Unidade produtiva",
    )

    class Meta:
        model = ElectricMotor
        fields = [
            "mo",
            "description",
            "unidade",
            "location_name",
            "power",
            "manufacturer",
            "frame",
            "rpm",
            "voltage",
            "current",
            "status",
            "notes",
        ]
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["unidade"].queryset = _visible_unidades_queryset(
            user=user,
            current_unidade_id=getattr(self.instance, "unidade_id", None),
        )
        self.fields["location_name"].label = "Local / setor"

        visible_unidades = list(self.fields["unidade"].queryset)
        if len(visible_unidades) == 1 and not self.instance.pk:
            self.fields["unidade"].initial = visible_unidades[0]

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("unidade") is None:
            self.add_error("unidade", "Selecione a unidade produtiva do motor.")
        return cleaned_data


class ElectricMotorFilterForm(forms.Form):
    search = forms.CharField(required=False, label="Busca textual")
    manufacturer = forms.CharField(required=False, label="Fabricante")
    fabrica = forms.ChoiceField(required=False, label="Fabrica")
    unidade = forms.ChoiceField(required=False, label="Unidade produtiva")
    status = forms.ChoiceField(required=False, label="Status")

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        visible_fabricas = list(get_fabricas_visiveis(user)) if user is not None else []
        visible_unidades = list(get_unidades_visiveis(user)) if user is not None else []
        self.fields["fabrica"].choices = [("", "Todas as fabricas")] + [
            (str(fabrica.code), fabrica.name) for fabrica in visible_fabricas
        ]
        self.fields["unidade"].choices = [("", "Todas as unidades")] + [
            (str(unidade.id), f"{unidade.fabrica.name} - {unidade.name}") for unidade in visible_unidades
        ]
        self.fields["status"].choices = [("", "Todos os status")] + list(MotorStatus.choices)


class BurnedMotorProcessForm(forms.ModelForm):
    class Meta:
        model = BurnedMotorProcess
        fields = [
            "occurred_at",
            "problem_type",
            "description",
            "sent_to_pcm",
            "sent_to_pcm_at",
            "in_quotation",
            "status",
            "payment_approved",
            "approved_at",
            "arrived",
            "arrived_at",
            "sent_for_rewinding",
            "third_party_company",
            "notes",
        ]
        widgets = {
            "occurred_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "sent_to_pcm_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "approved_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "arrived_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "description": forms.Textarea(attrs={"rows": 4}),
            "notes": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["occurred_at"].initial = self.instance.occurred_at if self.instance.pk else timezone.now()
        self.fields["status"].choices = list(MotorBurnoutFlowStatus.choices)

    def clean(self):
        cleaned_data = super().clean()
        sent_to_pcm = cleaned_data.get("sent_to_pcm")
        sent_to_pcm_at = cleaned_data.get("sent_to_pcm_at")
        payment_approved = cleaned_data.get("payment_approved")
        approved_at = cleaned_data.get("approved_at")
        arrived = cleaned_data.get("arrived")
        arrived_at = cleaned_data.get("arrived_at")

        if sent_to_pcm_at and not sent_to_pcm:
            self.add_error("sent_to_pcm", "Marque o envio para PCM quando houver data de envio.")
        if approved_at and not payment_approved:
            self.add_error("payment_approved", "Marque o pagamento aprovado quando houver data de aprovacao.")
        if arrived_at and not arrived:
            self.add_error("arrived", "Marque a chegada quando houver data de chegada.")
        return cleaned_data


class BurnedMotorCaseFilterForm(forms.Form):
    search = forms.CharField(required=False, label="Busca textual")
    status = forms.ChoiceField(required=False, label="Status")
    process_stage = forms.ChoiceField(required=False, label="Etapa do processo")
    fabrica = forms.ChoiceField(required=False, label="Fabrica")
    unidade = forms.ChoiceField(required=False, label="Unidade produtiva")
    location = forms.CharField(required=False, label="Local / setor")
    start_date = forms.DateField(required=False, label="De", widget=forms.DateInput(attrs={"type": "date"}))
    end_date = forms.DateField(required=False, label="Ate", widget=forms.DateInput(attrs={"type": "date"}))

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        visible_fabricas = list(get_fabricas_visiveis(user)) if user is not None else []
        visible_unidades = list(get_unidades_visiveis(user)) if user is not None else []
        self.fields["status"].choices = [("", "Todos os status")] + list(BurnedMotorCaseStatus.choices)
        self.fields["process_stage"].choices = PROCESS_STAGE_CHOICES
        self.fields["fabrica"].choices = [("", "Todas as fabricas")] + [
            (str(fabrica.code), fabrica.name) for fabrica in visible_fabricas
        ]
        self.fields["unidade"].choices = [("", "Todas as unidades")] + [
            (str(unidade.id), f"{unidade.fabrica.name} - {unidade.name}") for unidade in visible_unidades
        ]


class BurnedMotorCaseForm(forms.ModelForm):
    motor_lookup = MotorCatalogChoiceField(
        queryset=ElectricMotor.objects.none(),
        required=False,
        label="Motor cadastrado (opcional)",
    )
    unidade = UnidadeProdutivaChoiceField(
        queryset=UnidadeProdutiva.objects.none(),
        required=False,
        label="Unidade produtiva",
    )
    create_provisional_motor = forms.BooleanField(
        required=False,
        label="Criar cadastro provisÃ³rio do motor",
    )

    class Meta:
        model = BurnedMotorCase
        fields = [
            "unidade",
            "motor_description",
            "motor_mo",
            "motor_power",
            "motor_manufacturer",
            "motor_frame",
            "motor_rpm",
            "motor_voltage",
            "motor_current",
            "motor_location",
            "occurred_at",
            "requester_name",
            "problem_type",
            "defect_description",
            "technical_notes",
            "priority",
            "needs_pcm",
            "sent_to_pcm",
            "sent_to_pcm_at",
            "pcm_responsible",
            "sent_to_finance",
            "finance_sent_at",
            "approved",
            "approved_at",
            "solution_type",
            "purchase_new_motor",
            "rewinding_required",
            "third_party_company",
            "third_party_contact",
            "freight_requested",
            "pickup_at",
            "expected_return_at",
            "arrived_at",
            "progress_notes",
            "status",
        ]
        widgets = {
            "occurred_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "sent_to_pcm_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "finance_sent_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "approved_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "pickup_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "expected_return_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "arrived_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "defect_description": forms.Textarea(attrs={"rows": 4}),
            "technical_notes": forms.Textarea(attrs={"rows": 4}),
            "progress_notes": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        self.area = kwargs.pop("area", None)
        super().__init__(*args, **kwargs)
        self.fields["create_provisional_motor"].label = "Criar cadastro provisorio do motor"

        visible_unidades = _visible_unidades_queryset(
            user=self.user,
            current_unidade_id=getattr(self.instance, "unidade_id", None),
        )
        motor_queryset = (
            ElectricMotor.objects.select_related("area", "unidade", "unidade__fabrica")
            .filter(area=self.area, unidade__in=visible_unidades)
            .order_by("mo")
            if self.area is not None
            else ElectricMotor.objects.none()
        )
        if self.instance.pk and self.instance.motor_id:
            motor_queryset = ElectricMotor.objects.select_related("area", "unidade", "unidade__fabrica").filter(
                Q(pk__in=motor_queryset.values("pk")) | Q(pk=self.instance.motor_id)
            )
        self.fields["motor_lookup"].queryset = motor_queryset.distinct().order_by("mo")
        self.fields["unidade"].queryset = visible_unidades
        self.fields["occurred_at"].initial = self.instance.occurred_at if self.instance.pk else timezone.now()
        self.fields["status"].choices = list(BurnedMotorCaseStatus.choices)
        self.fields["priority"].choices = list(BurnedMotorPriority.choices)
        self.fields["solution_type"].choices = list(MotorSolutionType.choices)

        if self.instance.pk:
            self.fields["motor_lookup"].initial = self.instance.motor
            self.fields["unidade"].initial = self.instance.resolved_unidade
            self.fields["create_provisional_motor"].initial = bool(
                self.instance.motor_id and getattr(self.instance.motor, "is_provisional", False)
            )
        else:
            visible_unidades_list = list(visible_unidades)
            if len(visible_unidades_list) == 1:
                self.fields["unidade"].initial = visible_unidades_list[0]

    def clean(self):
        cleaned_data = super().clean()
        selected_motor = cleaned_data.get("motor_lookup")
        unidade = cleaned_data.get("unidade")

        if selected_motor and selected_motor.unidade_id:
            if unidade and unidade.id != selected_motor.unidade_id:
                self.add_error("unidade", "A unidade produtiva precisa corresponder ao motor selecionado.")
            elif not unidade:
                cleaned_data["unidade"] = selected_motor.unidade
                unidade = selected_motor.unidade

        if unidade is None:
            self.add_error("unidade", "Selecione a unidade produtiva do processo.")

        for field_name, messages in validate_burned_case_form_data(cleaned_data).items():
            for message in messages:
                self.add_error(field_name, message)
        return cleaned_data


class BurnedMotorCaseStatusForm(forms.Form):
    status = forms.ChoiceField(label="Novo status")
    progress_notes = forms.CharField(
        required=False,
        label="Observacao da atualizacao",
        widget=forms.Textarea(attrs={"rows": 3}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["status"].choices = list(BurnedMotorCaseStatus.choices)


def _visible_unidades_queryset(*, user=None, current_unidade_id=None):
    base_queryset = (
        get_unidades_visiveis(user)
        if user is not None
        else UnidadeProdutiva.objects.select_related("fabrica").order_by("fabrica__name", "name")
    )
    if current_unidade_id:
        return (
            UnidadeProdutiva.objects.select_related("fabrica")
            .filter(Q(pk__in=base_queryset.values("pk")) | Q(pk=current_unidade_id))
            .order_by("fabrica__name", "name")
        )
    return base_queryset.order_by("fabrica__name", "name")
