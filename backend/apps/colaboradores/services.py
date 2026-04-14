from __future__ import annotations

from urllib.parse import urlencode

from django.core.paginator import Paginator
from django.db.models import Q

from apps.colaboradores.models import Collaborator
from apps.unidades.models import Area
from apps.unidades.services import get_fabricas_visiveis, get_unidades_visiveis
from common.enums import RecordStatus
from common.permissions import ensure_area_access, get_allowed_areas, is_global_user


def active_collaborators():
    return Collaborator.objects.filter(status=RecordStatus.ACTIVE).select_related("area", "linked_user")


def resolve_team_area(user, area_code: str | None):
    if area_code:
        area = Area.objects.filter(code=area_code).first()
        ensure_area_access(user, area)
        return area

    preferred_area = getattr(user, "area", None)
    if preferred_area is not None:
        ensure_area_access(user, preferred_area)
        return preferred_area

    allowed_areas = [area for area in get_allowed_areas(user) if area is not None]
    if allowed_areas:
        area = allowed_areas[0]
        ensure_area_access(user, area)
        return area
    return None


def serialize_query_without_page(querydict) -> str:
    data = querydict.copy()
    if "page" in data:
        data.pop("page")
    return urlencode(data, doseq=True)


def base_team_queryset(user, *, area=None):
    queryset = Collaborator.objects.select_related(
        "area",
        "linked_user",
        "linked_user__role",
        "linked_user__fabrica",
        "linked_user__unidade",
        "linked_user__unidade__fabrica",
    ).order_by("full_name")
    if area is not None:
        return queryset.filter(area=area)
    if is_global_user(user):
        return queryset
    allowed_areas = get_allowed_areas(user)
    if allowed_areas:
        return queryset.filter(area__in=allowed_areas)
    return queryset.none()


def apply_team_filters(queryset, cleaned_data: dict):
    search = cleaned_data.get("search")
    job_title = cleaned_data.get("job_title")
    status = cleaned_data.get("status")
    fabrica_code = cleaned_data.get("fabrica")
    unidade_id = cleaned_data.get("unidade")

    if search:
        queryset = queryset.filter(
            Q(full_name__icontains=search)
            | Q(registration_number__icontains=search)
            | Q(job_title__icontains=search)
            | Q(linked_user__full_name__icontains=search)
            | Q(linked_user__email__icontains=search)
        )
    if job_title:
        queryset = queryset.filter(job_title__icontains=job_title)
    if status:
        queryset = queryset.filter(status=status)
    if fabrica_code:
        queryset = queryset.filter(
            Q(linked_user__fabrica__code=fabrica_code)
            | Q(linked_user__unidade__fabrica__code=fabrica_code)
        )
    if unidade_id:
        queryset = queryset.filter(linked_user__unidade_id=unidade_id)
    return queryset


def apply_team_physical_scope(queryset, user):
    visible_unidades = list(get_unidades_visiveis(user).values_list("id", flat=True))
    visible_fabricas = list(get_fabricas_visiveis(user).values_list("id", flat=True))

    if visible_unidades:
        return queryset.filter(
            Q(linked_user__isnull=True)
            | Q(linked_user__unidade_id__in=visible_unidades)
            | Q(linked_user__unidade__isnull=True, linked_user__fabrica_id__in=visible_fabricas)
        )

    if visible_fabricas:
        return queryset.filter(
            Q(linked_user__isnull=True)
            | Q(linked_user__fabrica_id__in=visible_fabricas)
            | Q(linked_user__unidade__fabrica_id__in=visible_fabricas)
        )

    return queryset


def paginate_team_queryset(queryset, page_number: str | int | None, per_page: int = 12):
    return Paginator(queryset, per_page).get_page(page_number)


def build_team_summary(queryset):
    linked_count = queryset.exclude(linked_user__isnull=True).count()
    return {
        "total_count": queryset.count(),
        "active_count": queryset.filter(status=RecordStatus.ACTIVE).count(),
        "linked_count": linked_count,
        "unlinked_count": queryset.filter(linked_user__isnull=True).count(),
        "fabrica_count": queryset.filter(
            Q(linked_user__fabrica__isnull=False) | Q(linked_user__unidade__fabrica__isnull=False)
        )
        .values_list("linked_user__fabrica__code", "linked_user__unidade__fabrica__code")
        .distinct()
        .count(),
        "unidade_count": queryset.exclude(linked_user__unidade__isnull=True).values_list("linked_user__unidade_id", flat=True).distinct().count(),
    }
