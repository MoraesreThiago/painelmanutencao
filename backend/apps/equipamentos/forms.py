from __future__ import annotations

from django import forms
from django.db.models import Q
from django.utils import timezone

from apps.equipamentos.models import Equipment, Motor
from apps.unidades.models import Area, Location, UnidadeProdutiva
from apps.unidades.services import get_fabricas_visiveis, get_unidades_visiveis
from common.enums import EquipmentStatus, EquipmentType
from common.permissions import get_allowed_areas


class UnidadeProdutivaChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return f"{obj.fabrica.name} - {obj.name}"


def _current_area_queryset(allowed_areas):
    if allowed_areas:
        return Area.objects.filter(id__in=[area.id for area in allowed_areas]).order_by("name")
    return Area.objects.order_by("name")


def _current_unidade_queryset(*, user=None, current_unidade_id=None):
    if user is not None:
        queryset = get_unidades_visiveis(user)
    else:
        queryset = UnidadeProdutiva.objects.select_related("fabrica").order_by("fabrica__name", "name")

    if current_unidade_id:
        queryset = (
            UnidadeProdutiva.objects.select_related("fabrica")
            .filter(Q(pk__in=queryset.values("pk")) | Q(pk=current_unidade_id))
            .order_by("fabrica__name", "name")
        )
    return queryset


def _current_location_queryset(*, allowed_areas, user=None, current_location_id=None):
    queryset = Location.objects.select_related("area", "unidade", "unidade__fabrica")
    if allowed_areas:
        queryset = queryset.filter(area__in=allowed_areas)
    if user is not None:
        visible_unidades = get_unidades_visiveis(user)
        queryset = queryset.filter(unidade__in=visible_unidades)
    if current_location_id:
        queryset = queryset.filter(Q(pk__in=queryset.values("pk")) | Q(pk=current_location_id))
    return queryset.order_by("area__name", "unidade__fabrica__name", "unidade__name", "name")


class EquipmentForm(forms.ModelForm):
    unidade = UnidadeProdutivaChoiceField(
        queryset=UnidadeProdutiva.objects.none(),
        required=False,
        label="Unidade produtiva",
    )

    class Meta:
        model = Equipment
        fields = [
            "code",
            "tag",
            "description",
            "sector",
            "manufacturer",
            "model",
            "serial_number",
            "type",
            "status",
            "registered_at",
            "area",
            "unidade",
            "location",
            "notes",
        ]
        widgets = {
            "registered_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "notes": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, user=None, allowed_areas=None, **kwargs):
        super().__init__(*args, **kwargs)
        if allowed_areas is None and user is not None:
            allowed_areas = get_allowed_areas(user)
        allowed_areas = list(allowed_areas or [])

        self.fields["registered_at"].required = False
        self.fields["registered_at"].initial = self.instance.registered_at if self.instance.pk else timezone.now()
        self.fields["type"].label = "Classificacao"

        self.fields["area"].queryset = _current_area_queryset(allowed_areas)
        self.fields["unidade"].queryset = _current_unidade_queryset(
            user=user,
            current_unidade_id=getattr(self.instance, "unidade_id", None),
        )
        self.fields["location"].queryset = _current_location_queryset(
            allowed_areas=allowed_areas,
            user=user,
            current_location_id=getattr(self.instance, "location_id", None),
        )

        if len(allowed_areas) == 1 and not self.instance.pk:
            self.fields["area"].initial = allowed_areas[0]

        visible_unidades = list(self.fields["unidade"].queryset)
        if len(visible_unidades) == 1 and not self.instance.pk:
            self.fields["unidade"].initial = visible_unidades[0]

    def clean(self):
        cleaned_data = super().clean()
        area = cleaned_data.get("area")
        unidade = cleaned_data.get("unidade")
        location = cleaned_data.get("location")

        if location and area and location.area_id != area.id:
            self.add_error("location", "A unidade/local selecionada nao pertence a area informada.")

        if location and location.unidade_id:
            if unidade and location.unidade_id != unidade.id:
                self.add_error("location", "O local selecionado nao pertence a unidade produtiva informada.")
            elif not unidade:
                cleaned_data["unidade"] = location.unidade
                unidade = location.unidade

        if unidade is None:
            self.add_error("unidade", "Selecione a unidade produtiva do equipamento.")

        if not cleaned_data.get("registered_at"):
            cleaned_data["registered_at"] = timezone.now()
        return cleaned_data


class EquipmentFilterForm(forms.Form):
    equipment_name = forms.CharField(required=False, label="Nome do equipamento")
    tag_name = forms.CharField(required=False, label="Nome da TAG")
    area = forms.ChoiceField(required=False, label="Area")
    fabrica = forms.ChoiceField(required=False, label="Fabrica")
    unidade = forms.ChoiceField(required=False, label="Unidade produtiva")
    location = forms.ChoiceField(required=False, label="Local")
    equipment_type = forms.ChoiceField(required=False, label="Classificacao")
    status = forms.ChoiceField(required=False, label="Status")

    def __init__(self, *args, user=None, allowed_areas=None, **kwargs):
        super().__init__(*args, **kwargs)
        allowed_areas = list(allowed_areas or [])
        visible_fabricas = list(get_fabricas_visiveis(user)) if user is not None else []
        visible_unidades = list(get_unidades_visiveis(user)) if user is not None else []
        locations = _current_location_queryset(allowed_areas=allowed_areas, user=user)

        self.fields["area"].choices = [("", "Todas as areas")] + [
            (str(area.code), area.name) for area in allowed_areas
        ]
        self.fields["fabrica"].choices = [("", "Todas as fabricas")] + [
            (str(fabrica.code), fabrica.name) for fabrica in visible_fabricas
        ]
        self.fields["unidade"].choices = [("", "Todas as unidades")] + [
            (str(unidade.id), f"{unidade.fabrica.name} - {unidade.name}") for unidade in visible_unidades
        ]
        self.fields["location"].choices = [("", "Todos os locais")] + [
            (str(location.id), f"{location.unidade.name if location.unidade else '-'} - {location.name}")
            for location in locations
        ]
        self.fields["equipment_type"].choices = [("", "Todas as classificacoes")] + list(EquipmentType.choices)
        self.fields["status"].choices = [("", "Todos os status")] + list(EquipmentStatus.choices)


class MotorForm(forms.ModelForm):
    class Meta:
        model = Motor
        fields = ["unique_identifier", "current_status", "last_internal_service_at", "electric_motor"]
        widgets = {
            "last_internal_service_at": forms.DateInput(attrs={"type": "date"}),
            "electric_motor": forms.Select(attrs={"class": "form-select"}),
        }
        labels = {
            "electric_motor": "Motor elétrico do catálogo (opcional)",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.motores.models import ElectricMotor

        self.fields["electric_motor"].empty_label = "— nenhum (motor sem catálogo técnico)"
        self.fields["electric_motor"].queryset = ElectricMotor.objects.order_by("mo")
