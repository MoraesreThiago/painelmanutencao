from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from states.permissions import has_permission


SYSTEM_SECTION = "Sistema"
AREA_SWITCHER_SECTION = "Areas"
PRINCIPAL_SECTION = "Principal"
SERVICES_SECTION = "Servicos"
REPORTS_SECTION = "Relatorios"
MANAGEMENT_SECTION = "Gestao"


@dataclass(frozen=True)
class NavigationItem:
    route: str
    label: str
    permission: str | None = None
    area_code: str | None = None
    section: str | None = None
    slot: str | None = None
    visible_in_menu: bool = True


SYSTEM_NAV_ITEMS = [
    NavigationItem(route="/dashboard", label="Dashboard", permission="view_dashboard", section=SYSTEM_SECTION),
    NavigationItem(route="/users", label="Usuarios", permission="view_users", section=SYSTEM_SECTION, visible_in_menu=False),
]

AREA_SWITCHER_ITEMS = [
    NavigationItem(route="/electrical", label="Eletrica", permission="view_area_data", area_code="ELETRICA", section=AREA_SWITCHER_SECTION, slot="home"),
    NavigationItem(route="/instrumentation", label="Instrumentacao", permission="view_area_data", area_code="INSTRUMENTACAO", section=AREA_SWITCHER_SECTION, slot="home"),
    NavigationItem(route="/mechanical", label="Mecanica", permission="view_area_data", area_code="MECANICA", section=AREA_SWITCHER_SECTION, slot="home"),
]

AREA_NAV_ITEMS = [
    NavigationItem(route="/electrical", label="Painel principal", permission="view_dashboard", area_code="ELETRICA", section=PRINCIPAL_SECTION, slot="home"),
    NavigationItem(route="/electrical/occurrences", label="Ocorrencias", permission="view_area_data", area_code="ELETRICA", section=PRINCIPAL_SECTION, slot="occurrences"),
    NavigationItem(route="/electrical/history", label="Historico", permission="view_area_data", area_code="ELETRICA", section=PRINCIPAL_SECTION, slot="history"),
    NavigationItem(route="/electrical/equipments", label="Equipamentos", permission="view_area_data", area_code="ELETRICA", section=PRINCIPAL_SECTION, slot="equipments"),
    NavigationItem(route="/electrical/service-orders", label="Ordem de servico", permission="view_area_data", area_code="ELETRICA", section=SERVICES_SECTION, slot="service_orders"),
    NavigationItem(route="/electrical/services/motors", label="Motores eletricos", permission="view_area_data", area_code="ELETRICA", section=SERVICES_SECTION, slot="service_assets"),
    NavigationItem(route="/electrical/reports/monthly", label="Relatorio mensal", permission="view_reports", area_code="ELETRICA", section=REPORTS_SECTION, slot="monthly_report"),
    NavigationItem(route="/electrical/management/collaborators", label="Colaboradores", permission="manage_area_data", area_code="ELETRICA", section=MANAGEMENT_SECTION, slot="collaborators"),
    NavigationItem(route="/instrumentation", label="Painel principal", permission="view_dashboard", area_code="INSTRUMENTACAO", section=PRINCIPAL_SECTION, slot="home"),
    NavigationItem(route="/instrumentation/occurrences", label="Ocorrencias", permission="view_area_data", area_code="INSTRUMENTACAO", section=PRINCIPAL_SECTION, slot="occurrences"),
    NavigationItem(route="/instrumentation/history", label="Historico", permission="view_area_data", area_code="INSTRUMENTACAO", section=PRINCIPAL_SECTION, slot="history"),
    NavigationItem(route="/instrumentation/equipments", label="Equipamentos", permission="view_area_data", area_code="INSTRUMENTACAO", section=PRINCIPAL_SECTION, slot="equipments"),
    NavigationItem(route="/instrumentation/services/instruments", label="Instrumentos", permission="view_area_data", area_code="INSTRUMENTACAO", section=SERVICES_SECTION, slot="service_assets"),
    NavigationItem(route="/instrumentation/reports/monthly", label="Relatorio mensal", permission="view_reports", area_code="INSTRUMENTACAO", section=REPORTS_SECTION, slot="monthly_report"),
    NavigationItem(route="/instrumentation/management/collaborators", label="Colaboradores", permission="manage_area_data", area_code="INSTRUMENTACAO", section=MANAGEMENT_SECTION, slot="collaborators"),
    NavigationItem(route="/mechanical", label="Painel principal", permission="view_dashboard", area_code="MECANICA", section=PRINCIPAL_SECTION, slot="home"),
    NavigationItem(route="/mechanical/occurrences", label="Ocorrencias", permission="view_area_data", area_code="MECANICA", section=PRINCIPAL_SECTION, slot="occurrences"),
    NavigationItem(route="/mechanical/history", label="Historico", permission="view_area_data", area_code="MECANICA", section=PRINCIPAL_SECTION, slot="history"),
    NavigationItem(route="/mechanical/equipments", label="Equipamentos", permission="view_area_data", area_code="MECANICA", section=PRINCIPAL_SECTION, slot="equipments"),
    NavigationItem(route="/mechanical/reports/monthly", label="Relatorio mensal", permission="view_reports", area_code="MECANICA", section=REPORTS_SECTION, slot="monthly_report"),
    NavigationItem(route="/mechanical/management/collaborators", label="Colaboradores", permission="manage_area_data", area_code="MECANICA", section=MANAGEMENT_SECTION, slot="collaborators"),
]

ROUTE_ITEMS = {item.route: item for item in (*SYSTEM_NAV_ITEMS, *AREA_SWITCHER_ITEMS, *AREA_NAV_ITEMS)}

AREA_LABELS = {
    "ELETRICA": "Eletrica",
    "INSTRUMENTACAO": "Instrumentacao",
    "MECANICA": "Mecanica",
}


def get_area_label(area_code: str | None) -> str:
    if not area_code:
        return "Visao geral"
    return AREA_LABELS.get(area_code, area_code.title())


def route_area_code(route: str) -> str | None:
    item = ROUTE_ITEMS.get(route)
    return item.area_code if item else None


def _can_show_item(item: NavigationItem, permissions: list[str], area_codes: list[str]) -> bool:
    if not has_permission(permissions, item.permission):
        return False
    if item.area_code and item.area_code not in area_codes:
        return False
    return True


def _to_nav_dict(item: NavigationItem, active_route: str) -> dict[str, Any]:
    return {"route": item.route, "label": item.label, "active": item.route == active_route}


def build_system_nav(permissions: list[str], area_codes: list[str], active_route: str) -> list[dict[str, Any]]:
    return [
        _to_nav_dict(item, active_route)
        for item in SYSTEM_NAV_ITEMS
        if item.visible_in_menu and _can_show_item(item, permissions, area_codes)
    ]


def build_area_switcher_nav(permissions: list[str], area_codes: list[str], active_route: str) -> list[dict[str, Any]]:
    return [
        _to_nav_dict(item, active_route)
        for item in AREA_SWITCHER_ITEMS
        if _can_show_item(item, permissions, area_codes)
    ]


def build_area_sections(permissions: list[str], area_codes: list[str], area_code: str, active_route: str) -> list[dict[str, Any]]:
    sections: list[dict[str, Any]] = []
    for section_name in (PRINCIPAL_SECTION, SERVICES_SECTION, REPORTS_SECTION, MANAGEMENT_SECTION):
        items = [
            _to_nav_dict(item, active_route)
            for item in AREA_NAV_ITEMS
            if item.area_code == area_code
            and item.section == section_name
            and _can_show_item(item, permissions, area_codes)
        ]
        if items:
            sections.append({"title": section_name, "items": items})
    return sections


def _single_area_home_route(permissions: list[str], area_codes: list[str]) -> str | None:
    if len(area_codes) != 1:
        return None

    target_area_code = area_codes[0]
    for item in AREA_SWITCHER_ITEMS:
        if item.area_code == target_area_code and _can_show_item(item, permissions, area_codes):
            return item.route
    return None


def route_is_allowed(route: str, permissions: list[str], area_codes: list[str]) -> bool:
    if route in {"/", "/login"}:
        return True
    item = ROUTE_ITEMS.get(route)
    if item is None:
        return False
    return _can_show_item(item, permissions, area_codes)


def fallback_route(permissions: list[str], area_codes: list[str]) -> str:
    single_area_route = _single_area_home_route(permissions, area_codes)
    if single_area_route:
        return single_area_route

    for item in SYSTEM_NAV_ITEMS:
        if item.route == "/dashboard" and _can_show_item(item, permissions, area_codes):
            return item.route
    for item in AREA_SWITCHER_ITEMS:
        if _can_show_item(item, permissions, area_codes):
            return item.route
    return "/login"


