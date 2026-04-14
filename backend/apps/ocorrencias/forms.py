from __future__ import annotations

from django import forms
from django.db.models import Q
from django.utils import timezone

from apps.colaboradores.models import Collaborator
from apps.equipamentos.models import Equipment
from apps.equipamentos.services import build_equipment_physical_scope_q
from apps.ocorrencias.models import Occurrence
from apps.ocorrencias.services import HISTORY_ACTION_CHOICES
from apps.unidades.models import Area, Location
from apps.unidades.services import get_fabricas_visiveis, get_unidades_visiveis
from common.enums import OccurrenceClassification, OccurrenceStatus, RecordStatus
from common.permissions import get_allowed_areas


def _current_location_queryset(*, allowed_areas, user=None, current_location_id=None):
    queryset = Location.objects.select_related("area", "unidade", "unidade__fabrica")
    if allowed_areas:
        queryset = queryset.filter(area__in=allowed_areas)
    if user is not None:
        queryset = queryset.filter(Q(unidade__in=get_unidades_visiveis(user)) | Q(pk=current_location_id))
    elif current_location_id:
        queryset = queryset.filter(Q(pk=current_location_id) | Q(pk__in=queryset.values("pk")))
    return queryset.order_by("area__name", "unidade__fabrica__name", "unidade__name", "name")


class OccurrenceForm(forms.ModelForm):
    area = forms.ModelChoiceField(queryset=Area.objects.none(), required=False, label="Area")

    class Meta:
        model = Occurrence
        fields = [
            "area",
            "equipment",
            "location",
            "classification",
            "responsible_collaborator",
            "occurred_at",
            "had_downtime",
            "downtime_minutes",
            "description",
            "notes",
        ]
        widgets = {
            "occurred_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "description": forms.Textarea(attrs={"rows": 4}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, user=None, allowed_areas=None, initial_equipment=None, **kwargs):
        super().__init__(*args, **kwargs)
        if allowed_areas is None and user is not None:
            allowed_areas = get_allowed_areas(user)
        allowed_areas = list(allowed_areas or [])

        if initial_equipment and not self.instance.pk:
            self.fields["equipment"].initial = initial_equipment
            self.fields["area"].initial = initial_equipment.area
            self.fields["location"].initial = initial_equipment.location

        self.fields["occurred_at"].required = False
        self.fields["occurred_at"].initial = self.instance.occurred_at if self.instance.pk else timezone.now()

        if allowed_areas:
            area_ids = [area.id for area in allowed_areas]
            self.fields["area"].queryset = Area.objects.filter(id__in=area_ids).order_by("name")
            equipment_queryset = Equipment.objects.filter(area_id__in=area_ids)
            if user is not None:
                equipment_queryset = equipment_queryset.filter(build_equipment_physical_scope_q(user))
            if self.instance.pk:
                equipment_queryset = equipment_queryset.filter(Q(pk__in=equipment_queryset.values("pk")) | Q(pk=self.instance.equipment_id))
            self.fields["equipment"].queryset = equipment_queryset.order_by("code").distinct()
            self.fields["location"].queryset = _current_location_queryset(
                allowed_areas=allowed_areas,
                user=user,
                current_location_id=getattr(self.instance, "location_id", None),
            )
            self.fields["responsible_collaborator"].queryset = Collaborator.objects.filter(
                area_id__in=area_ids,
                status=RecordStatus.ACTIVE,
            ).order_by("full_name")
            if len(allowed_areas) == 1 and not self.instance.pk and not self.initial.get("area"):
                self.fields["area"].initial = allowed_areas[0]
        else:
            self.fields["area"].queryset = Area.objects.order_by("name")
            self.fields["equipment"].queryset = Equipment.objects.select_related("area").order_by("code")
            self.fields["location"].queryset = _current_location_queryset(
                allowed_areas=allowed_areas,
                user=user,
                current_location_id=getattr(self.instance, "location_id", None),
            )
            self.fields["responsible_collaborator"].queryset = Collaborator.objects.filter(
                status=RecordStatus.ACTIVE
            ).select_related("area").order_by("full_name")

        self.fields["classification"].label = "Classificacao"
        self.fields["responsible_collaborator"].label = "Responsavel"
        self.fields["had_downtime"].label = "Houve parada"
        self.fields["downtime_minutes"].label = "Tempo de parada (min)"

    def clean(self):
        cleaned_data = super().clean()
        equipment = cleaned_data.get("equipment")
        area = cleaned_data.get("area")
        location = cleaned_data.get("location")
        collaborator = cleaned_data.get("responsible_collaborator")

        if equipment and area and equipment.area_id != area.id:
            self.add_error("equipment", "O equipamento selecionado nao pertence a area informada.")
        if equipment and not area:
            cleaned_data["area"] = equipment.area
        if location and equipment and location.area_id != equipment.area_id:
            self.add_error("location", "A unidade/local precisa pertencer a mesma area do equipamento.")
        if location and equipment and location.unidade_id and equipment.resolved_unidade and location.unidade_id != equipment.resolved_unidade.id:
            self.add_error("location", "O local selecionado nao pertence a mesma unidade produtiva do equipamento.")
        if collaborator and equipment and collaborator.area_id != equipment.area_id:
            self.add_error("responsible_collaborator", "O responsavel precisa pertencer a mesma area do equipamento.")
        if not cleaned_data.get("occurred_at"):
            cleaned_data["occurred_at"] = timezone.now()
        if cleaned_data.get("had_downtime") is False:
            cleaned_data["downtime_minutes"] = None
        return cleaned_data


class OccurrenceFilterForm(forms.Form):
    search = forms.CharField(required=False, label="Busca")
    area = forms.ChoiceField(required=False, label="Area")
    fabrica = forms.ChoiceField(required=False, label="Fabrica")
    unidade = forms.ChoiceField(required=False, label="Unidade produtiva")
    location = forms.ChoiceField(required=False, label="Local")
    classification = forms.ChoiceField(required=False, label="Classificacao")
    status = forms.ChoiceField(required=False, label="Status")
    downtime = forms.ChoiceField(required=False, label="Parada")

    def __init__(self, *args, user=None, allowed_areas=None, **kwargs):
        super().__init__(*args, **kwargs)
        allowed_areas = list(allowed_areas or [])
        visible_fabricas = list(get_fabricas_visiveis(user)) if user is not None else []
        visible_unidades = list(get_unidades_visiveis(user)) if user is not None else []
        locations = _current_location_queryset(allowed_areas=allowed_areas, user=user)

        self.fields["area"].choices = [("", "Todas as areas")] + [(str(area.code), area.name) for area in allowed_areas]
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
        self.fields["classification"].choices = [("", "Todas as classificacoes")] + list(OccurrenceClassification.choices)
        self.fields["status"].choices = [("", "Todos os status")] + list(OccurrenceStatus.choices)
        self.fields["downtime"].choices = [
            ("", "Com e sem parada"),
            ("yes", "Com parada"),
            ("no", "Sem parada"),
        ]


class OccurrenceStatusForm(forms.Form):
    status = forms.ChoiceField(choices=OccurrenceStatus.choices, label="Novo status")
    note = forms.CharField(required=False, label="Observacao da atualizacao", widget=forms.Textarea(attrs={"rows": 2}))


class OccurrenceHistoryFilterForm(forms.Form):
    search = forms.CharField(required=False, label="Busca")
    area = forms.ChoiceField(required=False, label="Area")
    action = forms.ChoiceField(required=False, label="Evento")

    def __init__(self, *args, allowed_areas=None, **kwargs):
        super().__init__(*args, **kwargs)
        allowed_areas = list(allowed_areas or [])
        self.fields["area"].choices = [("", "Todas as areas")] + [(str(area.code), area.name) for area in allowed_areas]
        self.fields["action"].choices = HISTORY_ACTION_CHOICES
