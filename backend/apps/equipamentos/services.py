from __future__ import annotations

from urllib.parse import urlencode

from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone

from apps.equipamentos.models import Equipment
from apps.unidades.models import Area
from apps.unidades.services import build_lookup_exact_q, build_user_unidade_scope_q
from common.enums import EquipmentStatus
from common.permissions import ensure_area_access, get_allowed_areas, is_global_user


def equipment_unidade_lookup_paths() -> tuple[str, ...]:
    return ("unidade_id", "location__unidade_id")


def equipment_fabrica_lookup_paths() -> tuple[str, ...]:
    return ("unidade__fabrica__code", "location__unidade__fabrica__code")


def build_equipment_physical_scope_q(user) -> Q:
    return build_user_unidade_scope_q(
        user,
        equipment_unidade_lookup_paths(),
        include_unassigned_for_broad_scope=True,
    )


def base_equipment_queryset(user):
    queryset = Equipment.objects.select_related(
        "area",
        "unidade",
        "unidade__fabrica",
        "location",
        "location__area",
        "location__unidade",
        "location__unidade__fabrica",
        "motor",
        "instrument",
    ).order_by("code")

    if not is_global_user(user):
        allowed_areas = get_allowed_areas(user)
        if not allowed_areas:
            return queryset.none()
        queryset = queryset.filter(area__in=allowed_areas)

    return queryset.filter(build_equipment_physical_scope_q(user)).distinct()


def resolve_area_from_code(user, area_code: str | None):
    if not area_code:
        return None
    area = Area.objects.filter(code=area_code).first()
    ensure_area_access(user, area)
    return area


def apply_equipment_filters(queryset, cleaned_data: dict):
    equipment_name = cleaned_data.get("equipment_name")
    tag_name = cleaned_data.get("tag_name")
    area_code = cleaned_data.get("area")
    fabrica_code = cleaned_data.get("fabrica")
    unidade_id = cleaned_data.get("unidade")
    location_id = cleaned_data.get("location")
    equipment_type = cleaned_data.get("equipment_type")
    status = cleaned_data.get("status")

    if equipment_name:
        queryset = queryset.filter(
            Q(description__icontains=equipment_name)
            | Q(code__icontains=equipment_name)
        )
    if tag_name:
        queryset = queryset.filter(tag__icontains=tag_name)
    if area_code:
        queryset = queryset.filter(area__code=area_code)
    if fabrica_code:
        queryset = queryset.filter(build_lookup_exact_q(equipment_fabrica_lookup_paths(), fabrica_code))
    if unidade_id:
        queryset = queryset.filter(build_lookup_exact_q(equipment_unidade_lookup_paths(), unidade_id))
    if location_id:
        queryset = queryset.filter(location_id=location_id)
    if equipment_type:
        queryset = queryset.filter(type=equipment_type)
    if status:
        queryset = queryset.filter(status=status)
    return queryset.distinct()


def paginate_equipment_queryset(queryset, page_number: str | int | None, per_page: int = 12):
    return Paginator(queryset, per_page).get_page(page_number)


def serialize_query_without_page(querydict) -> str:
    data = querydict.copy()
    if "page" in data:
        data.pop("page")
    return urlencode(data, doseq=True)


def _normalize_equipment_scope(equipment: Equipment):
    if equipment.location_id and equipment.location.area_id != equipment.area_id:
        raise ValueError("A unidade/local precisa pertencer a mesma area do equipamento.")
    if equipment.location_id and equipment.location.unidade_id:
        if equipment.unidade_id and equipment.unidade_id != equipment.location.unidade_id:
            raise ValueError("O local selecionado nao pertence a unidade produtiva informada.")
        if not equipment.unidade_id:
            equipment.unidade = equipment.location.unidade
    if not equipment.unidade_id:
        raise ValueError("Selecione a unidade produtiva do equipamento.")


def create_equipment_from_form(form):
    equipment = form.save(commit=False)
    if not equipment.registered_at:
        equipment.registered_at = timezone.now()
    _normalize_equipment_scope(equipment)
    equipment.save()
    return equipment


def update_equipment_from_form(form):
    equipment = form.save(commit=False)
    if not equipment.registered_at:
        equipment.registered_at = timezone.now()
    _normalize_equipment_scope(equipment)
    equipment.save()
    return equipment


def toggle_equipment_active_state(equipment: Equipment):
    equipment.status = EquipmentStatus.INACTIVE if equipment.status != EquipmentStatus.INACTIVE else EquipmentStatus.ACTIVE
    equipment.save(update_fields=["status", "updated_at"])
    return equipment
