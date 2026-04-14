from __future__ import annotations

from datetime import timedelta

from django.db.models import Count, Q, Sum
from django.urls import reverse
from django.utils import timezone

from apps.equipamentos.models import Equipment, Instrument
from apps.ocorrencias.models import Movement, Occurrence
from apps.ordens_servico.models import ExternalServiceOrder
from common.enums import (
    AreaCode,
    EquipmentStatus,
    EquipmentType,
    ExternalServiceStatus,
    InstrumentStatus,
    OccurrenceClassification,
    OccurrenceStatus,
)
from common.permissions import (
    PermissionName,
    can_manage_team,
    can_view_area_data,
    can_view_reports,
    get_actual_user_role_name,
    get_allowed_areas,
    get_user_role_name,
    has_permission,
    is_assuming_role_context,
)


def _route_name_for_area(area) -> str:
    if area is None:
        return "access:dashboard"
    return {
        AreaCode.ELETRICA: "access:workspace-eletrica",
        AreaCode.INSTRUMENTACAO: "access:workspace-instrumentacao",
        AreaCode.MECANICA: "access:workspace-mecanica",
    }.get(area.code, "access:dashboard")


def build_panel_href(area=None) -> str:
    base_url = reverse("access:area-dashboard")
    if area is None:
        return base_url
    return f"{base_url}?area={area.code}"


def _nav_item(slug: str, label: str, href: str, *, active_slug: str, is_disabled: bool = False) -> dict:
    return {
        "slug": slug,
        "label": label,
        "icon_slug": slug,
        "href": href,
        "is_active": active_slug == slug,
        "is_disabled": is_disabled,
    }


def is_electrical_context(user, area=None) -> bool:
    if area is not None:
        return area.code == AreaCode.ELETRICA
    if getattr(user, "area", None) is not None:
        return user.area.code == AreaCode.ELETRICA
    allowed_areas = get_allowed_areas(user)
    if len(allowed_areas) == 1:
        return allowed_areas[0].code == AreaCode.ELETRICA
    return False


def build_current_context_summary(user, area=None) -> dict:
    actual_role = get_actual_user_role_name(user)
    effective_role = get_user_role_name(user)
    return {
        "area_label": area.name if area is not None else "-",
        "actual_role_label": actual_role.label if actual_role else "-",
        "effective_role_label": effective_role.label if effective_role else "-",
        "is_assumed": is_assuming_role_context(user),
    }


def build_sidebar_sections(user, *, active_slug: str = "painel", area=None) -> list[dict]:
    primary_url = build_panel_href(area)
    sections: list[dict] = []
    electrical_context = is_electrical_context(user, area=area)
    principal_items = [_nav_item("painel", "Painel Principal", primary_url, active_slug=active_slug)]
    if can_view_area_data(user):
        equipamentos_url = reverse("equipamentos:list")
        equipe_url = reverse("colaboradores:team")
        motores_url = reverse("motores:list")
        motores_queimados_url = reverse("motores:burned-case-list")
        ocorrencias_url = reverse("ocorrencias:list")
        historico_url = reverse("ocorrencias:history")
        assistente_url = reverse("assistente:chat")
        ordens_url = reverse("ordens-servico:list")
        energia_url = reverse("access:power-monitoring")
        if area is not None:
            equipamentos_url = f"{equipamentos_url}?area={area.code}"
            equipe_url = f"{equipe_url}?area={area.code}"
            motores_url = f"{motores_url}?area={area.code}"
            motores_queimados_url = f"{motores_queimados_url}?area={area.code}"
            ocorrencias_url = f"{ocorrencias_url}?area={area.code}"
            historico_url = f"{historico_url}?area={area.code}"
            assistente_url = f"{assistente_url}?area={area.code}"
            ordens_url = f"{ordens_url}?area={area.code}"
            energia_url = f"{energia_url}?area={area.code}"
        principal_items.extend(
            [
                _nav_item("ocorrencias", "Ocorrências", ocorrencias_url, active_slug=active_slug),
                _nav_item("ordens", "Ordens de Serviço", ordens_url, active_slug=active_slug),
                _nav_item("historico", "Histórico", historico_url, active_slug=active_slug),
            ]
        )
        if can_manage_team(user):
            principal_items.append(_nav_item("equipe", "Equipe", equipe_url, active_slug=active_slug))
    sections.append({"title": "Principal", "items": principal_items})

    if can_view_area_data(user):
        asset_items = [
            _nav_item("equipamentos", "Equipamentos", equipamentos_url, active_slug=active_slug),
        ]
        if electrical_context:
            asset_items.append(_nav_item("motores", "Motores Elétricos", motores_url, active_slug=active_slug))
            if has_permission(user, PermissionName.MANAGE_AREA_DATA):
                asset_items.append(
                    _nav_item(
                        "motores-queimados",
                        "Motores Queimados",
                        motores_queimados_url,
                        active_slug=active_slug,
                    )
                )
        sections.append(
            {
                "title": "Ativos",
                "items": asset_items,
            }
        )
        if electrical_context:
            sections.append(
                {
                    "title": "Energia",
                    "items": [
                        _nav_item(
                            "energia",
                            "Tensão, Geração e Consumo",
                            energia_url,
                            active_slug=active_slug,
                        )
                    ],
                }
            )
        sections.append(
            {
                "title": "Assistente",
                "items": [
                    _nav_item("assistente", "Chat IA", assistente_url, active_slug=active_slug),
                ],
            }
        )

    if can_view_reports(user):
        summary_url = reverse("access:monthly-summary")
        if area is not None:
            summary_url = f"{summary_url}?area={area.code}"
        sections.append(
            {
                "title": "Relatórios",
                "items": [
                    _nav_item(
                        "relatorios",
                        "Resumo Mensal",
                        summary_url,
                        active_slug=active_slug,
                    )
                ],
            }
        )
    return sections


def build_power_monitoring_payload(area=None) -> dict:
    eyebrow = area.name if area is not None else "Energia"
    metrics = [
        {
            "key": "concessionaria",
            "label": "Tensão da concessionária",
            "value": "--",
            "description": "Visão das três fases da entrada da concessionária.",
        },
        {
            "key": "consumo",
            "label": "Consumo da fábrica",
            "value": "--",
            "description": "Aguardando integração com o totalizador de consumo da planta.",
        },
        {
            "key": "geracao",
            "label": "Geração da turbina",
            "value": "--",
            "description": "Aguardando integração com os dados operacionais da turbina.",
        },
    ]
    concessionaire_phases = [
        {
            "label": "Fase R",
            "value": "--",
            "description": "Leitura dedicada da fase R da concessionária.",
        },
        {
            "label": "Fase S",
            "value": "--",
            "description": "Leitura dedicada da fase S da concessionária.",
        },
        {
            "label": "Fase T",
            "value": "--",
            "description": "Leitura dedicada da fase T da concessionária.",
        },
    ]
    monitoring_cards = [
        {
            "title": "Tensão da concessionária",
            "description": "Aqui serão mostrados os gráficos do histórico das tensões das fases R, S e T da concessionária.",
            "chart_title": "Gráfico histórico da tensão da concessionária",
            "chart_caption": "Histórico por período com comparação entre as três fases.",
        },
        {
            "title": "Consumo da fábrica",
            "description": "Aqui serão mostrados os gráficos do histórico do consumo da fábrica ao longo do tempo.",
            "chart_title": "Gráfico histórico do consumo da fábrica",
            "chart_caption": "Evolução do consumo com base no período selecionado.",
        },
        {
            "title": "Geração da turbina",
            "description": "Aqui serão mostrados os gráficos do histórico da geração da turbina.",
            "chart_title": "Gráfico histórico da geração da turbina",
            "chart_caption": "Acompanhamento da geração própria e sua variação ao longo do tempo.",
        },
    ]
    return {
        "eyebrow": eyebrow,
        "metrics": metrics,
        "concessionaire_phases": concessionaire_phases,
        "monitoring_cards": monitoring_cards,
    }


def build_dashboard_payload(user, area=None) -> dict:
    equipment_qs = Equipment.objects.all()
    occurrence_qs = Occurrence.objects.select_related("equipment", "area")
    movements_qs = Movement.objects.select_related("equipment", "new_location", "moved_by_user")
    orders_qs = ExternalServiceOrder.objects.select_related("motor__equipment")
    instruments_qs = Instrument.objects.select_related("equipment")

    if area is not None:
        equipment_qs = equipment_qs.filter(area=area)
        occurrence_qs = occurrence_qs.filter(area=area)
        movements_qs = movements_qs.filter(equipment__area=area)
        orders_qs = orders_qs.filter(motor__equipment__area=area)
        instruments_qs = instruments_qs.filter(equipment__area=area)
    else:
        allowed_areas = get_allowed_areas(user)
        if allowed_areas:
            equipment_qs = equipment_qs.filter(area__in=allowed_areas)
            occurrence_qs = occurrence_qs.filter(area__in=allowed_areas)
            movements_qs = movements_qs.filter(equipment__area__in=allowed_areas)
            orders_qs = orders_qs.filter(motor__equipment__area__in=allowed_areas)
            instruments_qs = instruments_qs.filter(equipment__area__in=allowed_areas)
        else:
            equipment_qs = equipment_qs.none()
            occurrence_qs = occurrence_qs.none()
            movements_qs = movements_qs.none()
            orders_qs = orders_qs.none()
            instruments_qs = instruments_qs.none()

    now = timezone.now()
    overdue_returns = orders_qs.filter(
        expected_return_at__lt=now,
        service_status__in=[
            ExternalServiceStatus.OPEN,
            ExternalServiceStatus.IN_PROGRESS,
            ExternalServiceStatus.DELAYED,
        ],
    ).count()
    calibration_due = instruments_qs.filter(
        calibration_due_date__lte=(now + timedelta(days=30)).date()
    ).exclude(current_status=InstrumentStatus.INACTIVE).count()
    open_occurrences = occurrence_qs.filter(
        status__in=[
            OccurrenceStatus.OPEN,
            OccurrenceStatus.IN_PROGRESS,
            OccurrenceStatus.WAITING_PARTS,
        ]
    ).count()

    area_summary = list(
        equipment_qs.values("area__name")
        .annotate(
            equipment_count=Count("id"),
            motor_count=Count("id", filter=Q(type=EquipmentType.MOTOR)),
            instrument_count=Count("id", filter=Q(type=EquipmentType.INSTRUMENT)),
        )
        .order_by("area__name")
    )

    alerts = []
    if overdue_returns:
        alerts.append(
            {
                "title": "OS externa atrasada",
                "description": f"{overdue_returns} ordem(ns) externas estao com retorno fora do prazo.",
            }
        )
    if calibration_due:
        alerts.append(
            {
                "title": "Calibracoes proximas",
                "description": f"{calibration_due} instrumento(s) precisam de atencao nos proximos 30 dias.",
            }
        )
    if open_occurrences:
        alerts.append(
            {
                "title": "Ocorrencias em aberto",
                "description": f"{open_occurrences} ocorrencia(s) precisam de acompanhamento operacional.",
            }
        )
    if not alerts:
        alerts.append({"title": "Operacao estavel", "description": "Nao ha alertas criticos no momento."})

    return {
        "metrics": [
            {"label": "Equipamentos", "value": equipment_qs.count()},
            {"label": "Ocorrencias abertas", "value": open_occurrences},
            {"label": "Motores", "value": equipment_qs.filter(type=EquipmentType.MOTOR).count()},
            {"label": "Instrumentos", "value": equipment_qs.filter(type=EquipmentType.INSTRUMENT).count()},
            {"label": "Servico externo", "value": equipment_qs.filter(status=EquipmentStatus.EXTERNAL_SERVICE).count()},
            {"label": "Retornos atrasados", "value": overdue_returns},
        ],
        "alerts": alerts,
        "recent_movements": list(movements_qs.order_by("-moved_at")[:8]),
        "area_summary": area_summary,
        "can_view_reports": has_permission(user, PermissionName.VIEW_REPORTS)
        or has_permission(user, PermissionName.VIEW_GLOBAL_REPORTS),
    }


def build_monthly_summary_payload(user, area=None) -> dict:
    equipment_qs = Equipment.objects.select_related("area", "location")
    occurrence_qs = Occurrence.objects.select_related("equipment", "area", "location")
    orders_qs = ExternalServiceOrder.objects.select_related("motor__equipment")

    if area is not None:
        equipment_qs = equipment_qs.filter(area=area)
        occurrence_qs = occurrence_qs.filter(area=area)
        orders_qs = orders_qs.filter(motor__equipment__area=area)
    else:
        allowed_areas = get_allowed_areas(user)
        if allowed_areas:
            equipment_qs = equipment_qs.filter(area__in=allowed_areas)
            occurrence_qs = occurrence_qs.filter(area__in=allowed_areas)
            orders_qs = orders_qs.filter(motor__equipment__area__in=allowed_areas)
        else:
            equipment_qs = equipment_qs.none()
            occurrence_qs = occurrence_qs.none()
            orders_qs = orders_qs.none()

    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if month_start.month == 12:
        next_month = month_start.replace(year=month_start.year + 1, month=1)
    else:
        next_month = month_start.replace(month=month_start.month + 1)

    month_occurrences = occurrence_qs.filter(occurred_at__gte=month_start, occurred_at__lt=next_month)
    month_orders = orders_qs.filter(created_at__gte=month_start, created_at__lt=next_month)

    status_summary = [
        {"label": OccurrenceStatus(item["status"]).label, "total": item["total"]}
        for item in month_occurrences.values("status").annotate(total=Count("id")).order_by("-total", "status")
    ]
    classification_summary = [
        {"label": OccurrenceClassification(item["classification"]).label, "total": item["total"]}
        for item in month_occurrences.values("classification")
        .annotate(total=Count("id"))
        .order_by("-total", "classification")
    ]
    area_summary = list(
        month_occurrences.values("area__name")
        .annotate(total=Count("id"))
        .order_by("-total", "area__name")
    )

    downtime_minutes = month_occurrences.aggregate(total=Sum("downtime_minutes"))["total"] or 0

    return {
        "reference_month": month_start,
        "metrics": [
            {"label": "Ocorrencias no mes", "value": month_occurrences.count()},
            {"label": "Resolvidas no mes", "value": month_occurrences.filter(status=OccurrenceStatus.RESOLVED).count()},
            {"label": "Tempo de parada", "value": downtime_minutes},
            {"label": "Motores ativos", "value": equipment_qs.filter(type=EquipmentType.MOTOR, status=EquipmentStatus.ACTIVE).count()},
            {"label": "Equipamentos ativos", "value": equipment_qs.filter(status=EquipmentStatus.ACTIVE).count()},
            {"label": "OS externas no mes", "value": month_orders.count()},
        ],
        "status_summary": status_summary,
        "classification_summary": classification_summary,
        "area_summary": area_summary,
        "recent_occurrences": list(month_occurrences.order_by("-occurred_at")[:8]),
    }
