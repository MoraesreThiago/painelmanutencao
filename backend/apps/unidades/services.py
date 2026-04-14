from __future__ import annotations

from django.db.models import Q, QuerySet

from apps.unidades.models import Fabrica, UnidadeProdutiva
from common.enums import AreaCode, RoleName
from common.permissions import get_user_role_name


def _empty_fabricas_queryset() -> QuerySet[Fabrica]:
    return Fabrica.objects.none()


def _empty_unidades_queryset() -> QuerySet[UnidadeProdutiva]:
    return UnidadeProdutiva.objects.none()


def _is_supervisor_eletrica(user) -> bool:
    return get_user_role_name(user) == RoleName.SUPERVISOR and getattr(getattr(user, "area", None), "code", None) == AreaCode.ELETRICA


def _is_supervisor_instrumentacao(user) -> bool:
    return get_user_role_name(user) == RoleName.SUPERVISOR and getattr(getattr(user, "area", None), "code", None) == AreaCode.INSTRUMENTACAO


def _is_supervisor_mecanica(user) -> bool:
    return get_user_role_name(user) == RoleName.SUPERVISOR and getattr(getattr(user, "area", None), "code", None) == AreaCode.MECANICA


def has_broad_physical_scope(user) -> bool:
    if not getattr(user, "is_authenticated", False):
        return False
    effective_role = get_user_role_name(user)
    return effective_role in {RoleName.ADMIN, RoleName.GERENTE} or _is_supervisor_eletrica(user) or _is_supervisor_instrumentacao(user)


def get_fabricas_visiveis(user) -> QuerySet[Fabrica]:
    if not getattr(user, "is_authenticated", False):
        return _empty_fabricas_queryset()

    effective_role = get_user_role_name(user)
    queryset = Fabrica.objects.filter(is_active=True).order_by("name")

    if effective_role in {RoleName.ADMIN, RoleName.GERENTE}:
        return queryset

    if _is_supervisor_eletrica(user) or _is_supervisor_instrumentacao(user):
        return queryset

    if _is_supervisor_mecanica(user):
        if not user.fabrica_id:
            return _empty_fabricas_queryset()
        return queryset.filter(pk=user.fabrica_id)

    if effective_role in {RoleName.LIDER, RoleName.INSPETOR, RoleName.MANUTENTOR}:
        if not user.unidade_id:
            return _empty_fabricas_queryset()
        return queryset.filter(unidades_produtivas=user.unidade_id).distinct()

    return _empty_fabricas_queryset()


def get_unidades_visiveis(user) -> QuerySet[UnidadeProdutiva]:
    if not getattr(user, "is_authenticated", False):
        return _empty_unidades_queryset()

    effective_role = get_user_role_name(user)
    queryset = UnidadeProdutiva.objects.select_related("fabrica").filter(is_active=True, fabrica__is_active=True).order_by(
        "fabrica__name",
        "name",
    )

    if effective_role in {RoleName.ADMIN, RoleName.GERENTE}:
        return queryset

    if _is_supervisor_eletrica(user) or _is_supervisor_instrumentacao(user):
        return queryset

    if _is_supervisor_mecanica(user):
        if not user.fabrica_id:
            return _empty_unidades_queryset()
        return queryset.filter(fabrica_id=user.fabrica_id)

    if effective_role in {RoleName.LIDER, RoleName.INSPETOR, RoleName.MANUTENTOR}:
        if not user.unidade_id:
            return _empty_unidades_queryset()
        return queryset.filter(pk=user.unidade_id)

    return _empty_unidades_queryset()


def pode_acessar_unidade(user, unidade_id) -> bool:
    if not unidade_id:
        return False
    return get_unidades_visiveis(user).filter(pk=unidade_id).exists()


def get_fabrica_ids_visiveis(user) -> list[str]:
    return list(get_fabricas_visiveis(user).values_list("id", flat=True))


def get_unidade_ids_visiveis(user) -> list[str]:
    return list(get_unidades_visiveis(user).values_list("id", flat=True))


def _normalize_lookup_paths(lookup_paths: str | list[str] | tuple[str, ...]) -> list[str]:
    if isinstance(lookup_paths, str):
        return [lookup_paths]
    return list(lookup_paths)


def build_lookup_in_q(lookup_paths: str | list[str] | tuple[str, ...], values) -> Q:
    query = Q()
    for lookup_path in _normalize_lookup_paths(lookup_paths):
        query |= Q(**{f"{lookup_path}__in": values})
    return query


def build_lookup_exact_q(lookup_paths: str | list[str] | tuple[str, ...], value) -> Q:
    query = Q()
    for lookup_path in _normalize_lookup_paths(lookup_paths):
        query |= Q(**{lookup_path: value})
    return query


def build_lookup_all_null_q(lookup_paths: str | list[str] | tuple[str, ...]) -> Q:
    query = Q()
    for lookup_path in _normalize_lookup_paths(lookup_paths):
        query &= Q(**{f"{lookup_path}__isnull": True})
    return query


def build_user_unidade_scope_q(
    user,
    lookup_paths: str | list[str] | tuple[str, ...],
    *,
    include_unassigned_for_broad_scope: bool = False,
) -> Q:
    visible_unidade_ids = get_unidade_ids_visiveis(user)
    if not visible_unidade_ids:
        return Q(pk__in=[])

    query = build_lookup_in_q(lookup_paths, visible_unidade_ids)
    if include_unassigned_for_broad_scope and has_broad_physical_scope(user):
        query |= build_lookup_all_null_q(lookup_paths)
    return query
