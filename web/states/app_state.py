from __future__ import annotations

import unicodedata
from typing import Any

import reflex as rx

from services.api_client import BackendApiError
from services.auth_service import auth_service
from services.maintenance_service import maintenance_service
from utils.area_scope import filter_records_for_area
from utils.formatting import humanize, month_start, parse_datetime, short_datetime
from states.navigation import (
    build_area_sections,
    build_area_switcher_nav,
    build_system_nav,
    fallback_route,
    get_area_label,
    route_area_code,
    route_is_allowed,
)
from states.permissions import can_manage_collaborators, role_level


class AppState(rx.State):
    persistent_auth_token: str = rx.LocalStorage("", name="imp_reflex_auth_token", sync=True)
    session_auth_token: str = rx.SessionStorage("", name="imp_reflex_session_auth_token")
    remember_me_storage: str = rx.LocalStorage("false", name="imp_reflex_remember_me", sync=True)
    sidebar_collapsed: bool = False
    email: str = ""
    password: str = ""
    auth_error: str = ""
    login_loading: bool = False

    current_user_name: str = ""
    current_user_email: str = ""
    role_name: str = ""
    role_level_value: int = 0
    permissions: list[str] = []
    allowed_areas: list[dict[str, str]] = []
    accessible_area_codes: list[str] = []

    active_route: str = "/login"
    current_area_code: str = ""
    current_area_name: str = ""
    login_entry_route: str = "/login"
    login_target_route: str = ""
    login_area_code: str = ""

    system_nav_items: list[dict[str, Any]] = []
    area_switcher_items: list[dict[str, Any]] = []
    workspace_principal_items: list[dict[str, Any]] = []
    workspace_service_items: list[dict[str, Any]] = []
    workspace_report_items: list[dict[str, Any]] = []
    electrical_sections: list[dict[str, Any]] = []
    instrumentation_sections: list[dict[str, Any]] = []
    mechanical_sections: list[dict[str, Any]] = []
    electrical_principal_items: list[dict[str, Any]] = []
    electrical_service_items: list[dict[str, Any]] = []
    electrical_report_items: list[dict[str, Any]] = []
    electrical_management_items: list[dict[str, Any]] = []
    instrumentation_principal_items: list[dict[str, Any]] = []
    instrumentation_service_items: list[dict[str, Any]] = []
    instrumentation_report_items: list[dict[str, Any]] = []
    instrumentation_management_items: list[dict[str, Any]] = []
    mechanical_principal_items: list[dict[str, Any]] = []
    mechanical_service_items: list[dict[str, Any]] = []
    mechanical_report_items: list[dict[str, Any]] = []
    mechanical_management_items: list[dict[str, Any]] = []

    dashboard_loading: bool = False
    dashboard_error: str = ""
    dashboard_metrics: list[dict[str, str]] = []
    dashboard_alerts: list[dict[str, str]] = []
    dashboard_area_summary_rows: list[list[str]] = []
    dashboard_recent_movements_rows: list[list[str]] = []

    page_loading: bool = False
    page_error: str = ""
    page_title: str = ""
    page_subtitle: str = ""
    hero_title: str = ""
    hero_description: str = ""
    support_text: str = ""
    scope_badges: list[dict[str, str]] = []
    metric_cards: list[dict[str, str]] = []
    alert_cards: list[dict[str, str]] = []
    quick_links: list[dict[str, str]] = []
    primary_table_title: str = ""
    primary_table_columns: list[str] = []
    primary_table_rows: list[list[str]] = []
    secondary_table_title: str = ""
    secondary_table_columns: list[str] = []
    secondary_table_rows: list[list[str]] = []
    tertiary_table_title: str = ""
    tertiary_table_columns: list[str] = []
    tertiary_table_rows: list[list[str]] = []

    @rx.var(cache=True)
    def is_authenticated(self) -> bool:
        return bool(self._auth_token() and self.current_user_email)

    @rx.var(cache=True)
    def can_manage_collaborator_view(self) -> bool:
        return can_manage_collaborators(self.role_name, self.permissions)

    @rx.var(cache=True)
    def remember_me_enabled(self) -> bool:
        return self.remember_me_storage.lower() == "true"

    @rx.var(cache=True)
    def sidebar_width(self) -> str:
        return "92px" if self.sidebar_collapsed else "260px"

    @rx.var(cache=True)
    def main_canvas_width(self) -> str:
        return "calc(100vw - 92px)" if self.sidebar_collapsed else "calc(100vw - 260px)"

    @staticmethod
    def _normalize_profile_token(value: str) -> str:
        normalized = unicodedata.normalize("NFKD", value.strip().lower())
        return "".join(char for char in normalized if not unicodedata.combining(char))

    def _profile_identity_parts(self) -> list[str]:
        if not self.current_user_name:
            return []

        parts = [part for part in self.current_user_name.split() if part]
        if not parts:
            return []

        role_tokens = {
            "admin",
            "administrador",
            "gerente",
            "lider",
            "manutentor",
            "operador",
            "supervisor",
            "tecnico",
        }

        filtered_parts = list(parts)
        while filtered_parts and self._normalize_profile_token(filtered_parts[0]) in role_tokens:
            filtered_parts = filtered_parts[1:]

        return filtered_parts or parts

    @rx.var(cache=True)
    def profile_display_name(self) -> str:
        parts = self._profile_identity_parts()
        if not parts:
            return "Usuario"

        if len(parts) >= 2:
            candidate = f"{parts[0]} {parts[1]}"
            if len(candidate) <= 18:
                return candidate
        return parts[0]

    @rx.var(cache=True)
    def profile_initials(self) -> str:
        parts = self._profile_identity_parts()
        if not parts:
            return "U"

        initials = parts[0][0]
        if len(parts) > 1:
            initials += parts[1][0]
        return initials.upper()

    def _auth_token(self) -> str:
        return self.persistent_auth_token or self.session_auth_token

    def _clear_auth_tokens(self) -> None:
        self.persistent_auth_token = ""
        self.session_auth_token = ""

    def _persist_session(self) -> bool:
        return self.remember_me_enabled

    def _set_auth_token(self, token: str) -> None:
        if self._persist_session():
            self.persistent_auth_token = token
            self.session_auth_token = ""
            return

        self.session_auth_token = token
        self.persistent_auth_token = ""

    @staticmethod
    def _remember_me_from_form(form_data: dict[str, Any]) -> str:
        raw_value = str(form_data.get("remember_me") or "").lower()
        return "true" if raw_value in {"true", "on", "1", "yes"} else "false"

    def toggle_sidebar(self):
        self.sidebar_collapsed = not self.sidebar_collapsed

    def _clear_user_context(self) -> None:
        self.current_user_name = ""
        self.current_user_email = ""
        self.role_name = ""
        self.role_level_value = 0
        self.permissions = []
        self.allowed_areas = []
        self.accessible_area_codes = []
        self.current_area_code = ""
        self.current_area_name = ""
        self.system_nav_items = []
        self.area_switcher_items = []
        self.workspace_principal_items = []
        self.workspace_service_items = []
        self.workspace_report_items = []
        self.electrical_sections = []
        self.instrumentation_sections = []
        self.mechanical_sections = []
        self.electrical_principal_items = []
        self.electrical_service_items = []
        self.electrical_report_items = []
        self.electrical_management_items = []
        self.instrumentation_principal_items = []
        self.instrumentation_service_items = []
        self.instrumentation_report_items = []
        self.instrumentation_management_items = []
        self.mechanical_principal_items = []
        self.mechanical_service_items = []
        self.mechanical_report_items = []
        self.mechanical_management_items = []

    def _set_login_context(
        self,
        *,
        entry_route: str,
        target_route: str = "",
        area_code: str = "",
    ) -> None:
        self.login_entry_route = entry_route
        self.login_target_route = target_route
        self.login_area_code = area_code
        self.auth_error = ""
        self.login_loading = False
        self._set_route_context(entry_route)

    def _reset_module_page(self) -> None:
        self.page_error = ""
        self.page_title = ""
        self.page_subtitle = ""
        self.hero_title = ""
        self.hero_description = ""
        self.support_text = ""
        self.scope_badges = []
        self.metric_cards = []
        self.alert_cards = []
        self.quick_links = []
        self.primary_table_title = ""
        self.primary_table_columns = []
        self.primary_table_rows = []
        self.secondary_table_title = ""
        self.secondary_table_columns = []
        self.secondary_table_rows = []
        self.tertiary_table_title = ""
        self.tertiary_table_columns = []
        self.tertiary_table_rows = []

    def _serialize_area(self, area: dict) -> dict[str, str]:
        return {"id": str(area["id"]), "name": area["name"], "code": area["code"]}

    def _apply_user_context(self, user: dict) -> None:
        role = user.get("role") or {}
        primary_area = user.get("area") or {}
        allowed_areas = user.get("allowed_areas") or []
        if not allowed_areas and primary_area:
            allowed_areas = [primary_area]

        serialized_areas = [
            self._serialize_area(area)
            for area in allowed_areas
            if isinstance(area, dict) and area.get("id") and area.get("code")
        ]

        self.current_user_name = user.get("full_name") or ""
        self.current_user_email = user.get("email") or ""
        self.role_name = role.get("name") or ""
        self.role_level_value = role_level(self.role_name)
        self.permissions = list(user.get("permissions") or [])
        self.allowed_areas = serialized_areas
        self.accessible_area_codes = [area["code"] for area in serialized_areas]
        self._rebuild_navigation()

    def _rebuild_navigation(self) -> None:
        self.system_nav_items = build_system_nav(self.permissions, self.accessible_area_codes, self.active_route)
        self.area_switcher_items = build_area_switcher_nav(self.permissions, self.accessible_area_codes, self.active_route)
        workspace_sections = self._build_workspace_nav_sections()
        self.workspace_principal_items = workspace_sections.get("Principal", [])
        self.workspace_service_items = workspace_sections.get("Servi\u00e7os", [])
        self.workspace_report_items = workspace_sections.get("Relat\u00f3rios", [])
        self.electrical_sections = build_area_sections(self.permissions, self.accessible_area_codes, "ELETRICA", self.active_route)
        self.instrumentation_sections = build_area_sections(self.permissions, self.accessible_area_codes, "INSTRUMENTACAO", self.active_route)
        self.mechanical_sections = build_area_sections(self.permissions, self.accessible_area_codes, "MECANICA", self.active_route)
        self.electrical_principal_items = self._section_items(self.electrical_sections, "Principal")
        self.electrical_service_items = self._section_items(self.electrical_sections, "Servicos")
        self.electrical_report_items = self._section_items(self.electrical_sections, "Relatorios")
        self.electrical_management_items = self._section_items(self.electrical_sections, "Gestao")
        self.instrumentation_principal_items = self._section_items(self.instrumentation_sections, "Principal")
        self.instrumentation_service_items = self._section_items(self.instrumentation_sections, "Servicos")
        self.instrumentation_report_items = self._section_items(self.instrumentation_sections, "Relatorios")
        self.instrumentation_management_items = self._section_items(self.instrumentation_sections, "Gestao")
        self.mechanical_principal_items = self._section_items(self.mechanical_sections, "Principal")
        self.mechanical_service_items = self._section_items(self.mechanical_sections, "Servicos")
        self.mechanical_report_items = self._section_items(self.mechanical_sections, "Relatorios")
        self.mechanical_management_items = self._section_items(self.mechanical_sections, "Gestao")

    @staticmethod
    def _section_items(sections: list[dict[str, Any]], title: str) -> list[dict[str, Any]]:
        for section in sections:
            if section.get("title") == title:
                return list(section.get("items") or [])
        return []

    def _build_workspace_nav_sections(self) -> dict[str, list[dict[str, Any]]]:
        section_map = {
            "ELETRICA": [
                {
                    "title": "Principal",
                    "items": [
                        ("/electrical", "Painel Principal", "house"),
                        ("/electrical/occurrences", "Ocorr\u00eancias", "triangle_alert"),
                        ("/electrical/history", "Hist\u00f3rico", "history"),
                        ("/electrical/equipments", "Equipamentos", "package"),
                    ],
                },
                {
                    "title": "Servi\u00e7os",
                    "items": [
                        ("/electrical/services/motors", "Motores El\u00e9tricos", "bolt"),
                    ],
                },
                {
                    "title": "Relat\u00f3rios",
                    "items": [
                        ("/electrical/reports/monthly", "Resumo Mensal", "file_text"),
                    ],
                },
            ],
            "INSTRUMENTACAO": [
                {
                    "title": "Principal",
                    "items": [
                        ("/instrumentation", "Painel Principal", "house"),
                        ("/instrumentation/occurrences", "Ocorr\u00eancias", "triangle_alert"),
                        ("/instrumentation/history", "Hist\u00f3rico", "history"),
                        ("/instrumentation/equipments", "Equipamentos", "package"),
                    ],
                },
                {
                    "title": "Servi\u00e7os",
                    "items": [
                        ("/instrumentation/services/instruments", "Instrumentos", "activity"),
                    ],
                },
                {
                    "title": "Relat\u00f3rios",
                    "items": [
                        ("/instrumentation/reports/monthly", "Resumo Mensal", "file_text"),
                    ],
                },
            ],
            "MECANICA": [
                {
                    "title": "Principal",
                    "items": [
                        ("/mechanical", "Painel Principal", "house"),
                        ("/mechanical/occurrences", "Ocorr\u00eancias", "triangle_alert"),
                        ("/mechanical/history", "Hist\u00f3rico", "history"),
                        ("/mechanical/equipments", "Equipamentos", "package"),
                    ],
                },
                {
                    "title": "Relat\u00f3rios",
                    "items": [
                        ("/mechanical/reports/monthly", "Resumo Mensal", "file_text"),
                    ],
                },
            ],
        }

        sections: dict[str, list[dict[str, Any]]] = {}
        for section in section_map.get(self.current_area_code, []):
            items: list[dict[str, Any]] = []
            for route, label, _icon in section["items"]:
                if not route_is_allowed(route, self.permissions, self.accessible_area_codes):
                    continue

                items.append(
                    {
                        "route": route,
                        "label": label,
                        "active": self.active_route == route,
                    }
                )

            if items:
                sections[section["title"]] = items

        return sections

    async def _load_electrical_service_orders(self, route: str):
        redirect = await self._prepare_route(route, "ELETRICA")
        if redirect:
            return redirect

        self.page_loading = True
        self.page_error = ""
        self._reset_module_page()

        try:
            service_orders = filter_records_for_area(
                await maintenance_service.list_external_service_orders(self._auth_token()),
                target_area_code="ELETRICA",
            )
        except BackendApiError as exc:
            self.page_error = str(exc)
            self.page_loading = False
            return

        open_statuses = {"OPEN", "IN_PROGRESS", "SENT"}
        self._set_module_page(
            title="Eletrica | Ordem de servico",
            subtitle="Acompanhamento das ordens de servico externas vinculadas aos motores da area.",
            hero_title="Ordem de servico com leitura operacional.",
            hero_description="Acompanhe envio, retorno e terceiros sem misturar essa leitura com as outras ocorrencias do modulo.",
            support_text="Esta tela reaproveita os registros reais de servico externo ja existentes no backend.",
            scope_badges=self._default_scope_badges("ELETRICA"),
            metric_cards=[
                {"label": "Ordens registradas", "value": str(len(service_orders)), "tone": "accent"},
                {
                    "label": "Ordens em aberto",
                    "value": str(sum(1 for item in service_orders if item.get("service_status") in open_statuses)),
                    "tone": "warning",
                },
            ],
            quick_links=self._quick_links_for_area("ELETRICA", route),
            primary_title="Ordens de servico",
            primary_columns=["OS", "Motor", "Equipamento", "Status", "Terceiro", "Envio"],
            primary_rows=[
                [
                    item["work_order_number"],
                    item["motor"]["unique_identifier"],
                    item["motor"]["equipment"]["code"],
                    item["service_status"],
                    item.get("vendor_name") or "-",
                    short_datetime(item.get("sent_at")),
                ]
                for item in service_orders
            ],
        )
        self.page_loading = False

    def _set_route_context(self, route: str, *, area_code: str | None = None) -> None:
        self.active_route = route
        resolved_area_code = area_code or route_area_code(route)
        self.current_area_code = resolved_area_code or ""
        self.current_area_name = get_area_label(resolved_area_code) if resolved_area_code else ""
        self._rebuild_navigation()

    def _area_by_code(self, area_code: str) -> dict[str, str] | None:
        for area in self.allowed_areas:
            if area["code"] == area_code:
                return area
        return None

    def _area_id_by_code(self, area_code: str) -> str | None:
        area = self._area_by_code(area_code)
        return area["id"] if area else None

    def _fallback_route(self) -> str:
        return fallback_route(self.permissions, self.accessible_area_codes)

    def _current_login_destination(self) -> str:
        if self.login_target_route and route_is_allowed(
            self.login_target_route,
            self.permissions,
            self.accessible_area_codes,
        ):
            if not self.login_area_code or self.login_area_code in self.accessible_area_codes:
                return self.login_target_route
        return self._fallback_route()

    async def _ensure_session(self) -> bool:
        if self.current_user_email:
            return True
        if not self._auth_token():
            return False
        try:
            user = await auth_service.current_user(self._auth_token())
        except BackendApiError:
            self._clear_auth_tokens()
            self._clear_user_context()
            return False
        self._apply_user_context(user)
        return True

    async def _prepare_route(self, route: str, area_code: str | None = None):
        authenticated = await self._ensure_session()
        if not authenticated:
            self._clear_user_context()
            self._set_route_context("/login")
            return rx.redirect("/login")

        if not route_is_allowed(route, self.permissions, self.accessible_area_codes):
            fallback = self._fallback_route()
            self._set_route_context(fallback)
            return rx.redirect(fallback)

        if area_code and area_code not in self.accessible_area_codes:
            fallback = self._fallback_route()
            self._set_route_context(fallback)
            return rx.redirect(fallback)

        self._set_route_context(route, area_code=area_code)
        return None

    def _default_scope_badges(self, area_code: str | None = None) -> list[dict[str, str]]:
        badges = [{"label": self.role_name or "Sem perfil", "tone": "info"}]
        if area_code:
            badges.append({"label": get_area_label(area_code), "tone": "accent"})
        return badges

    def _quick_links_for_area(self, area_code: str, current_route: str) -> list[dict[str, str]]:
        sections = build_area_sections(self.permissions, self.accessible_area_codes, area_code, current_route)
        links: list[dict[str, str]] = []
        for section in sections:
            for item in section["items"]:
                if item["route"] != current_route:
                    links.append({"label": item["label"], "route": item["route"]})
        return links[:6]

    async def load_root(self):
        if await self._ensure_session():
            fallback = self._fallback_route()
            self._set_route_context(fallback)
            return rx.redirect(fallback)
        self._set_login_context(entry_route="/login")
        return rx.redirect("/login")

    async def load_login_page(self):
        if await self._ensure_session():
            fallback = self._fallback_route()
            self._set_route_context(fallback)
            return rx.redirect(fallback)
        self._set_login_context(entry_route="/login")

    async def load_electrical_login_page(self):
        if await self._ensure_session():
            target_route = "/electrical"
            if route_is_allowed(target_route, self.permissions, self.accessible_area_codes):
                self._set_route_context(target_route, area_code="ELETRICA")
                return rx.redirect(target_route)

            fallback = self._fallback_route()
            self._set_route_context(fallback)
            return rx.redirect(fallback)

        self._set_login_context(
            entry_route="/login/electrical",
            target_route="/electrical",
            area_code="ELETRICA",
        )

    async def _submit_login_credentials(self) -> str | None:
        self.auth_error = ""
        try:
            payload = await auth_service.login(self.email.strip(), self.password)
            self._set_auth_token(payload["access_token"])
            user = await auth_service.current_user(self._auth_token())
        except BackendApiError as exc:
            self.auth_error = str(exc)
            return

        self._apply_user_context(user)

        if self.login_area_code and self.login_area_code not in self.accessible_area_codes:
            self._clear_auth_tokens()
            self._clear_user_context()
            self.auth_error = f"Seu usuario nao possui acesso a area {get_area_label(self.login_area_code)}."
            self._set_route_context(self.login_entry_route)
            return

        destination = self._current_login_destination()
        self._set_route_context(destination, area_code=route_area_code(destination))
        return destination

    async def submit_login_form(self, form_data: dict[str, Any]):
        if self.login_loading:
            return

        self.email = (form_data.get("email") or "").strip()
        self.password = form_data.get("password") or ""
        self.remember_me_storage = self._remember_me_from_form(form_data)
        self.login_loading = True
        yield

        destination = await self._submit_login_credentials()

        if destination:
            yield rx.redirect(destination)
            return

        self.login_loading = False

    def logout(self):
        self._clear_auth_tokens()
        self.auth_error = ""
        self._clear_user_context()
        self._set_login_context(entry_route="/login")
        return rx.redirect("/login")

    async def load_dashboard_page(self):
        redirect = await self._prepare_route("/dashboard")
        if redirect:
            return redirect

        self.dashboard_loading = True
        self.dashboard_error = ""
        try:
            dashboard = await maintenance_service.dashboard(self._auth_token())
        except BackendApiError as exc:
            self.dashboard_error = str(exc)
            self.dashboard_loading = False
            return

        self.dashboard_metrics = [
            {"label": metric["label"], "value": str(metric["value"]), "tone": "accent"}
            for metric in dashboard.get("metrics", [])
        ]
        self.dashboard_alerts = [
            {
                "title": alert["title"],
                "description": alert["description"],
                "tone": "danger" if alert["severity"] == "high" else "warning" if alert["severity"] == "medium" else "info",
            }
            for alert in dashboard.get("alerts", [])
        ]
        self.dashboard_area_summary_rows = [
            [item["area_name"], str(item["equipment_count"]), str(item["motor_count"]), str(item["instrument_count"])]
            for item in dashboard.get("area_summary", [])
        ]
        self.dashboard_recent_movements_rows = [
            [item["equipment_code"], item["equipment_description"], item.get("new_location") or "-", short_datetime(item.get("moved_at")), item["moved_by"], item["reason"]]
            for item in dashboard.get("recent_movements", [])
        ]
        self.dashboard_loading = False

    def _set_module_page(
        self,
        *,
        title: str,
        subtitle: str,
        hero_title: str,
        hero_description: str,
        support_text: str = "",
        scope_badges: list[dict[str, str]] | None = None,
        metric_cards: list[dict[str, str]] | None = None,
        alert_cards: list[dict[str, str]] | None = None,
        quick_links: list[dict[str, str]] | None = None,
        primary_title: str = "",
        primary_columns: list[str] | None = None,
        primary_rows: list[list[str]] | None = None,
        secondary_title: str = "",
        secondary_columns: list[str] | None = None,
        secondary_rows: list[list[str]] | None = None,
        tertiary_title: str = "",
        tertiary_columns: list[str] | None = None,
        tertiary_rows: list[list[str]] | None = None,
    ) -> None:
        self.page_title = title
        self.page_subtitle = subtitle
        self.hero_title = hero_title
        self.hero_description = hero_description
        self.support_text = support_text
        self.scope_badges = scope_badges or []
        self.metric_cards = metric_cards or []
        self.alert_cards = alert_cards or []
        self.quick_links = quick_links or []
        self.primary_table_title = primary_title
        self.primary_table_columns = primary_columns or []
        self.primary_table_rows = primary_rows or []
        self.secondary_table_title = secondary_title
        self.secondary_table_columns = secondary_columns or []
        self.secondary_table_rows = secondary_rows or []
        self.tertiary_table_title = tertiary_title
        self.tertiary_table_columns = tertiary_columns or []
        self.tertiary_table_rows = tertiary_rows or []

    async def _load_area_home(self, area_code: str, route: str):
        redirect = await self._prepare_route(route, area_code)
        if redirect:
            return redirect

        self.page_loading = True
        self.page_error = ""
        self._reset_module_page()
        area_id = self._area_id_by_code(area_code)

        try:
            dashboard = await maintenance_service.dashboard(self._auth_token(), area_id=area_id)
            extra_metrics: list[dict[str, str]] = []
            if area_code == "ELETRICA":
                motors = filter_records_for_area(await maintenance_service.list_motors(self._auth_token()), target_area_code=area_code)
                burned = filter_records_for_area(await maintenance_service.list_burned_motors(self._auth_token()), target_area_code=area_code)
                extra_metrics = [
                    {"label": "Motores eletricos", "value": str(len(motors)), "tone": "info"},
                    {"label": "Queimados em aberto", "value": str(sum(1 for item in burned if item["status"] not in {"REPAIRED", "DISCARDED"})), "tone": "warning"},
                ]
            elif area_code == "INSTRUMENTACAO":
                instruments = filter_records_for_area(await maintenance_service.list_instruments(self._auth_token()), target_area_code=area_code)
                requests = filter_records_for_area(await maintenance_service.list_instrument_service_requests(self._auth_token()), target_area_code=area_code)
                extra_metrics = [
                    {"label": "Instrumentos", "value": str(len(instruments)), "tone": "info"},
                    {"label": "Solicitacoes abertas", "value": str(sum(1 for item in requests if item["service_status"] not in {"COMPLETED", "CANCELLED"})), "tone": "warning"},
                ]

            metrics = [
                {"label": metric["label"], "value": str(metric["value"]), "tone": "accent"}
                for metric in dashboard.get("metrics", [])[:4]
            ] + extra_metrics
            alerts = [
                {
                    "title": alert["title"],
                    "description": alert["description"],
                    "tone": "danger" if alert["severity"] == "high" else "warning" if alert["severity"] == "medium" else "info",
                }
                for alert in dashboard.get("alerts", [])
            ]
            movements = [
                [item["equipment_code"], item["equipment_description"], item.get("new_location") or "-", short_datetime(item.get("moved_at")), item["moved_by"], item["reason"]]
                for item in dashboard.get("recent_movements", [])
            ]
        except BackendApiError as exc:
            self.page_error = str(exc)
            self.page_loading = False
            return

        area_label = get_area_label(area_code)
        self._set_module_page(
            title=area_label,
            subtitle=f"Painel principal da rotina operacional de {area_label.lower()}.",
            hero_title=f"Rotina operacional de {area_label.lower()} com leitura clara e acao rapida.",
            hero_description="Use este modulo para acompanhar ocorrencias, historico, ativos e relatorios do contexto atual.",
            support_text="O backend existente continua sendo a fonte de verdade; este frontend Reflex apenas consome os mesmos contratos de API e preserva o RBAC atual.",
            scope_badges=self._default_scope_badges(area_code),
            metric_cards=metrics[:6],
            alert_cards=alerts,
            quick_links=self._quick_links_for_area(area_code, route),
            primary_title="Movimentacoes recentes",
            primary_columns=["Equipamento", "Descricao", "Local", "Data", "Responsavel", "Motivo"],
            primary_rows=movements,
        )
        self.page_loading = False

    async def _load_area_occurrences(self, area_code: str, route: str):
        redirect = await self._prepare_route(route, area_code)
        if redirect:
            return redirect

        self.page_loading = True
        self.page_error = ""
        self._reset_module_page()
        area_label = get_area_label(area_code)

        try:
            if area_code == "ELETRICA":
                motors = filter_records_for_area(await maintenance_service.list_motors(self._auth_token()), target_area_code=area_code)
                replacements = filter_records_for_area(await maintenance_service.list_motor_replacements(self._auth_token()), target_area_code=area_code)
                burned = filter_records_for_area(await maintenance_service.list_burned_motors(self._auth_token()), target_area_code=area_code)
                service_orders = filter_records_for_area(await maintenance_service.list_external_service_orders(self._auth_token()), target_area_code=area_code)
                self._set_module_page(
                    title=f"{area_label} | Ocorrencias",
                    subtitle="Trocas de motores, backlog de queimados e servicos externos.",
                    hero_title="Leitura operacional da eletrica.",
                    hero_description="Este painel reaproveita os fluxos existentes de trocas de motor, queimados e ordens de servico.",
                    support_text="Nao foi criada uma entidade nova de ocorrencia. A visao continua ancorada nas entidades reais do backend.",
                    scope_badges=self._default_scope_badges(area_code),
                    metric_cards=[
                        {"label": "Motores eletricos", "value": str(len(motors)), "tone": "info"},
                        {"label": "Trocas registradas", "value": str(len(replacements)), "tone": "accent"},
                        {"label": "Backlog de queimados", "value": str(sum(1 for item in burned if item["status"] not in {"REPAIRED", "DISCARDED"})), "tone": "warning"},
                    ],
                    quick_links=self._quick_links_for_area(area_code, route),
                    primary_title="Trocas de motores",
                    primary_columns=["Tag", "Motor removido", "Motor instalado", "Motivo", "Data"],
                    primary_rows=[
                        [item["target_equipment_tag"], item["removed_motor"]["unique_identifier"], item["installed_motor"]["unique_identifier"], item["reason"], short_datetime(item.get("replaced_at"))]
                        for item in replacements
                    ],
                    secondary_title="Motores queimados",
                    secondary_columns=["Motor", "Tag de origem", "Diagnostico", "Status"],
                    secondary_rows=[
                        [item["motor"]["unique_identifier"], item["source_equipment_tag"], item["diagnosis"], humanize(item["status"])]
                        for item in burned
                    ],
                    tertiary_title="Servico externo",
                    tertiary_columns=["OS", "Equipamento", "Status", "Terceiro", "Data"],
                    tertiary_rows=[
                        [item["work_order_number"], item["motor"]["equipment"]["code"], item["service_status"], item.get("vendor_name") or "-", short_datetime(item.get("sent_at"))]
                        for item in service_orders
                    ],
                )
            elif area_code == "INSTRUMENTACAO":
                instruments = filter_records_for_area(await maintenance_service.list_instruments(self._auth_token()), target_area_code=area_code)
                replacements = filter_records_for_area(await maintenance_service.list_instrument_replacements(self._auth_token()), target_area_code=area_code)
                service_requests = filter_records_for_area(await maintenance_service.list_instrument_service_requests(self._auth_token()), target_area_code=area_code)
                self._set_module_page(
                    title=f"{area_label} | Ocorrencias",
                    subtitle="Trocas de instrumentos, manutencao, calibracao e terceiros.",
                    hero_title="Leitura operacional da instrumentacao.",
                    hero_description="A visao de ocorrencias continua baseada nas trocas e solicitacoes de servico que ja existem no sistema.",
                    support_text="A migracao preserva o dominio atual e nao duplica regra de negocio no frontend.",
                    scope_badges=self._default_scope_badges(area_code),
                    metric_cards=[
                        {"label": "Instrumentos", "value": str(len(instruments)), "tone": "info"},
                        {"label": "Trocas registradas", "value": str(len(replacements)), "tone": "accent"},
                        {"label": "Solicitacoes abertas", "value": str(sum(1 for item in service_requests if item["service_status"] not in {"COMPLETED", "CANCELLED"})), "tone": "warning"},
                    ],
                    quick_links=self._quick_links_for_area(area_code, route),
                    primary_title="Trocas de instrumentos",
                    primary_columns=["Tag", "Instrumento removido", "Instrumento instalado", "Motivo", "Data"],
                    primary_rows=[
                        [item["target_equipment_tag"], item["removed_instrument"]["unique_identifier"], item["installed_instrument"]["unique_identifier"], item["reason"], short_datetime(item.get("replaced_at"))]
                        for item in replacements
                    ],
                    secondary_title="Solicitacoes de servico",
                    secondary_columns=["Instrumento", "Tipo", "Status", "Terceiro", "Previsao"],
                    secondary_rows=[
                        [item["instrument"]["unique_identifier"], humanize(item["service_type"]), humanize(item["service_status"]), item.get("vendor_name") or "-", short_datetime(item.get("expected_return_at"))]
                        for item in service_requests
                    ],
                )
            else:
                overview = await maintenance_service.mechanical_overview(self._auth_token())
                self._set_module_page(
                    title=f"{area_label} | Ocorrencias",
                    subtitle="Visao operacional da mecanica sobre ativos e rastreabilidade.",
                    hero_title="Leitura operacional da mecanica.",
                    hero_description="Nesta fase, o modulo mecanico segue coerente com o dominio atual, sem inventar fluxo novo.",
                    support_text="O painel mecanico reaproveita o overview dedicado da API e organiza ativos, equipe e movimentacoes.",
                    scope_badges=self._default_scope_badges(area_code),
                    metric_cards=[{"label": item["label"], "value": str(item["value"]), "tone": "accent"} for item in overview.get("metrics", [])],
                    quick_links=self._quick_links_for_area(area_code, route),
                    primary_title="Resumo por status",
                    primary_columns=["Status", "Total"],
                    primary_rows=[[humanize(item["status"]), str(item["total"])] for item in overview.get("status_summary", [])],
                    secondary_title="Movimentacoes recentes",
                    secondary_columns=["Equipamento", "Descricao", "Local", "Data", "Responsavel", "Status"],
                    secondary_rows=[
                        [item["equipment_code"], item["equipment_description"], item.get("new_location") or "-", short_datetime(item.get("moved_at")), item["moved_by"], humanize(item.get("status_after"))]
                        for item in overview.get("recent_movements", [])
                    ],
                    tertiary_title="Equipe vinculada",
                    tertiary_columns=["Nome", "Matricula", "Cargo", "Contato", "Status"],
                    tertiary_rows=[
                        [item["full_name"], item["registration_number"], item.get("job_title") or "-", item.get("contact_phone") or "-", humanize(item["status"])]
                        for item in overview.get("collaborators", [])
                    ] if self.can_manage_collaborator_view else [],
                )
        except BackendApiError as exc:
            self.page_error = str(exc)
            self.page_loading = False
            return

        self.page_loading = False

    async def _load_area_history(self, area_code: str, route: str):
        redirect = await self._prepare_route(route, area_code)
        if redirect:
            return redirect
        self.page_loading = True
        self.page_error = ""
        self._reset_module_page()
        try:
            movements = filter_records_for_area(await maintenance_service.list_movements(self._auth_token()), target_area_code=area_code)
        except BackendApiError as exc:
            self.page_error = str(exc)
            self.page_loading = False
            return

        current_month = month_start()
        monthly_total = sum(1 for item in movements if (parse_datetime(item.get("moved_at")) or current_month) >= current_month)
        area_label = get_area_label(area_code)
        self._set_module_page(
            title=f"{area_label} | Historico",
            subtitle="Visao consolidada da rastreabilidade da area.",
            hero_title="Linha do tempo operacional.",
            hero_description="Consulte o historico de movimentacoes e mudancas de localizacao do escopo atual.",
            support_text="Este modulo continua apoiado nas movimentacoes existentes do backend, sem camada paralela de auditoria.",
            scope_badges=self._default_scope_badges(area_code),
            metric_cards=[
                {"label": "Movimentacoes registradas", "value": str(len(movements)), "tone": "accent"},
                {"label": "Movimentacoes no mes", "value": str(monthly_total), "tone": "info"},
            ],
            quick_links=self._quick_links_for_area(area_code, route),
            primary_title="Historico consolidado",
            primary_columns=["Equipamento", "Novo local", "Data", "Responsavel", "Motivo", "Status"],
            primary_rows=[
                [item["equipment"]["code"], (item.get("new_location") or {}).get("name", "-"), short_datetime(item.get("moved_at")), (item.get("moved_by_user") or {}).get("full_name", "-"), item["reason"], humanize(item.get("status_after"))]
                for item in movements
            ],
        )
        self.page_loading = False

    async def _load_area_equipments(self, area_code: str, route: str):
        redirect = await self._prepare_route(route, area_code)
        if redirect:
            return redirect
        self.page_loading = True
        self.page_error = ""
        self._reset_module_page()
        try:
            equipments = filter_records_for_area(await maintenance_service.list_equipments(self._auth_token()), target_area_code=area_code)
        except BackendApiError as exc:
            self.page_error = str(exc)
            self.page_loading = False
            return

        area_label = get_area_label(area_code)
        self._set_module_page(
            title=f"{area_label} | Equipamentos",
            subtitle="Base comum de ativos e rastreabilidade da area.",
            hero_title="Equipamentos no contexto atual.",
            hero_description="Consulta operacional dos ativos vinculados a esta area.",
            support_text="O CRUD completo continua no backend e no frontend atual; esta primeira etapa em Reflex prioriza shell, sessao e leitura funcional.",
            scope_badges=self._default_scope_badges(area_code),
            metric_cards=[
                {"label": "Equipamentos", "value": str(len(equipments)), "tone": "accent"},
                {"label": "Ativos", "value": str(sum(1 for item in equipments if item["status"] == "ACTIVE")), "tone": "success"},
                {"label": "Em manutencao", "value": str(sum(1 for item in equipments if item["status"] == "UNDER_MAINTENANCE")), "tone": "warning"},
            ],
            quick_links=self._quick_links_for_area(area_code, route),
            primary_title="Lista de equipamentos",
            primary_columns=["Codigo", "Tag", "Descricao", "Setor", "Local", "Status"],
            primary_rows=[
                [item["code"], item.get("tag") or "-", item["description"], item["sector"], (item.get("location") or {}).get("name", "-"), humanize(item["status"])]
                for item in equipments
            ],
        )
        self.page_loading = False

    async def _load_area_service_assets(self, area_code: str, route: str):
        redirect = await self._prepare_route(route, area_code)
        if redirect:
            return redirect
        self.page_loading = True
        self.page_error = ""
        self._reset_module_page()

        try:
            if area_code == "ELETRICA":
                assets = filter_records_for_area(await maintenance_service.list_motors(self._auth_token()), target_area_code=area_code)
                title = "Motores eletricos"
                metric_label = "Motores"
                rows = [
                    [item["unique_identifier"], item["equipment"]["code"], item["equipment"].get("tag") or "-", item["equipment"].get("description") or "-", humanize(item["current_status"])]
                    for item in assets
                ]
            else:
                assets = filter_records_for_area(await maintenance_service.list_instruments(self._auth_token()), target_area_code=area_code)
                title = "Instrumentos"
                metric_label = "Instrumentos"
                rows = [
                    [item["unique_identifier"], item["equipment"]["code"], item["equipment"].get("tag") or "-", item["instrument_type"], humanize(item["current_status"])]
                    for item in assets
                ]
        except BackendApiError as exc:
            self.page_error = str(exc)
            self.page_loading = False
            return

        area_label = get_area_label(area_code)
        self._set_module_page(
            title=f"{area_label} | {title}",
            subtitle="Ativos de servico especificos da area.",
            hero_title=f"Consulta de {title.lower()} no contexto atual.",
            hero_description="Leitura rapida dos ativos tecnicos mais relevantes para a rotina desta area.",
            scope_badges=self._default_scope_badges(area_code),
            metric_cards=[{"label": metric_label, "value": str(len(assets)), "tone": "accent"}],
            quick_links=self._quick_links_for_area(area_code, route),
            primary_title=title,
            primary_columns=["Identificacao", "Codigo", "Tag", "Tipo/Descricao", "Status"],
            primary_rows=rows,
        )
        self.page_loading = False

    async def _load_area_collaborators(self, area_code: str, route: str):
        redirect = await self._prepare_route(route, area_code)
        if redirect:
            return redirect
        if not self.can_manage_collaborator_view:
            fallback = self._fallback_route()
            return rx.redirect(fallback)

        self.page_loading = True
        self.page_error = ""
        self._reset_module_page()
        try:
            collaborators = filter_records_for_area(await maintenance_service.list_collaborators(self._auth_token()), target_area_code=area_code)
        except BackendApiError as exc:
            self.page_error = str(exc)
            self.page_loading = False
            return

        area_label = get_area_label(area_code)
        self._set_module_page(
            title=f"{area_label} | Colaboradores",
            subtitle="Gestao da equipe vinculada ao contexto da area.",
            hero_title="Gestao operacional de colaboradores.",
            hero_description="Esta visao so aparece para perfis de nivel 2 ou superior, em coerencia com as permissoes do backend.",
            support_text="A inativacao e a edicao continuam tratadas no backend atual; esta etapa em Reflex foca a leitura e a navegacao por escopo.",
            scope_badges=self._default_scope_badges(area_code),
            metric_cards=[
                {"label": "Colaboradores", "value": str(len(collaborators)), "tone": "accent"},
                {"label": "Ativos", "value": str(sum(1 for item in collaborators if item["status"] == "ACTIVE")), "tone": "success"},
                {"label": "Inativos", "value": str(sum(1 for item in collaborators if item["status"] == "INACTIVE")), "tone": "warning"},
            ],
            quick_links=self._quick_links_for_area(area_code, route),
            primary_title="Equipe cadastrada",
            primary_columns=["Nome", "Matricula", "Cargo", "Contato", "Status"],
            primary_rows=[
                [item["full_name"], item["registration_number"], item.get("job_title") or "-", item.get("contact_phone") or "-", humanize(item["status"])]
                for item in collaborators
            ],
        )
        self.page_loading = False

    async def _load_area_report(self, area_code: str, route: str):
        redirect = await self._prepare_route(route, area_code)
        if redirect:
            return redirect
        self.page_loading = True
        self.page_error = ""
        self._reset_module_page()

        try:
            equipments = filter_records_for_area(await maintenance_service.list_equipments(self._auth_token()), target_area_code=area_code)
            movements = filter_records_for_area(await maintenance_service.list_movements(self._auth_token()), target_area_code=area_code)
            current_month = month_start()
            report_rows: list[tuple[Any, list[str]]] = []
            for movement in movements:
                when = parse_datetime(movement.get("moved_at"))
                if when and when >= current_month:
                    report_rows.append((when, ["Movimentacao", movement["equipment"]["code"], movement["reason"], humanize(movement.get("status_after")), short_datetime(movement.get("moved_at"))]))

            if area_code == "ELETRICA":
                replacements = filter_records_for_area(await maintenance_service.list_motor_replacements(self._auth_token()), target_area_code=area_code)
                burned = filter_records_for_area(await maintenance_service.list_burned_motors(self._auth_token()), target_area_code=area_code)
                service_orders = filter_records_for_area(await maintenance_service.list_external_service_orders(self._auth_token()), target_area_code=area_code)
                for item in replacements:
                    when = parse_datetime(item.get("replaced_at"))
                    if when and when >= current_month:
                        report_rows.append((when, ["Troca de motor", item["target_equipment_tag"], f'{item["removed_motor"]["unique_identifier"]} -> {item["installed_motor"]["unique_identifier"]}', item["reason"], short_datetime(item.get("replaced_at"))]))
                for item in burned:
                    when = parse_datetime(item.get("recorded_at"))
                    if when and when >= current_month:
                        report_rows.append((when, ["Motor queimado", item["source_equipment_tag"], item["motor"]["unique_identifier"], humanize(item["status"]), short_datetime(item.get("recorded_at"))]))
                for item in service_orders:
                    when = parse_datetime(item.get("sent_at"))
                    if when and when >= current_month:
                        report_rows.append((when, ["Servico externo", item["work_order_number"], item["motor"]["equipment"]["code"], item["service_status"], short_datetime(item.get("sent_at"))]))
            elif area_code == "INSTRUMENTACAO":
                replacements = filter_records_for_area(await maintenance_service.list_instrument_replacements(self._auth_token()), target_area_code=area_code)
                requests = filter_records_for_area(await maintenance_service.list_instrument_service_requests(self._auth_token()), target_area_code=area_code)
                for item in replacements:
                    when = parse_datetime(item.get("replaced_at"))
                    if when and when >= current_month:
                        report_rows.append((when, ["Troca de instrumento", item["target_equipment_tag"], f'{item["removed_instrument"]["unique_identifier"]} -> {item["installed_instrument"]["unique_identifier"]}', item["reason"], short_datetime(item.get("replaced_at"))]))
                for item in requests:
                    when = parse_datetime(item.get("requested_at"))
                    if when and when >= current_month:
                        report_rows.append((when, ["Solicitacao de servico", item["instrument"]["equipment"]["code"], item["reason"], humanize(item["service_status"]), short_datetime(item.get("requested_at"))]))

            report_rows.sort(key=lambda item: item[0], reverse=True)
        except BackendApiError as exc:
            self.page_error = str(exc)
            self.page_loading = False
            return

        area_label = get_area_label(area_code)
        self._set_module_page(
            title=f"{area_label} | Relatorio mensal",
            subtitle="Consolidado operacional mensal da area.",
            hero_title="Leitura mensal baseada nos dados reais do sistema.",
            hero_description="Este relatorio reutiliza os registros ja existentes no backend, sem criar uma camada paralela de BI.",
            support_text="A migracao para Reflex preserva o modelo atual: backend como fonte de verdade e frontend focado em visualizacao e experiencia.",
            scope_badges=self._default_scope_badges(area_code),
            metric_cards=[
                {"label": "Ativos monitorados", "value": str(len(equipments)), "tone": "accent"},
                {"label": "Eventos no mes", "value": str(len(report_rows)), "tone": "info"},
            ],
            quick_links=self._quick_links_for_area(area_code, route),
            primary_title="Eventos do mes",
            primary_columns=["Tipo", "Referencia", "Detalhe", "Status/Motivo", "Data"],
            primary_rows=[row for _, row in report_rows[:16]],
        )
        self.page_loading = False

    async def load_electrical_home(self):
        return await self._load_area_home("ELETRICA", "/electrical")

    async def load_instrumentation_home(self):
        return await self._load_area_home("INSTRUMENTACAO", "/instrumentation")

    async def load_mechanical_home(self):
        return await self._load_area_home("MECANICA", "/mechanical")

    async def load_electrical_occurrences(self):
        return await self._load_area_occurrences("ELETRICA", "/electrical/occurrences")

    async def load_instrumentation_occurrences(self):
        return await self._load_area_occurrences("INSTRUMENTACAO", "/instrumentation/occurrences")

    async def load_mechanical_occurrences(self):
        return await self._load_area_occurrences("MECANICA", "/mechanical/occurrences")

    async def load_electrical_history(self):
        return await self._load_area_history("ELETRICA", "/electrical/history")

    async def load_instrumentation_history(self):
        return await self._load_area_history("INSTRUMENTACAO", "/instrumentation/history")

    async def load_mechanical_history(self):
        return await self._load_area_history("MECANICA", "/mechanical/history")

    async def load_electrical_equipments(self):
        return await self._load_area_equipments("ELETRICA", "/electrical/equipments")

    async def load_instrumentation_equipments(self):
        return await self._load_area_equipments("INSTRUMENTACAO", "/instrumentation/equipments")

    async def load_mechanical_equipments(self):
        return await self._load_area_equipments("MECANICA", "/mechanical/equipments")

    async def load_electrical_services(self):
        return await self._load_area_service_assets("ELETRICA", "/electrical/services/motors")

    async def load_instrumentation_services(self):
        return await self._load_area_service_assets("INSTRUMENTACAO", "/instrumentation/services/instruments")

    async def load_electrical_service_orders(self):
        return await self._load_electrical_service_orders("/electrical/service-orders")

    async def load_electrical_collaborators(self):
        return await self._load_area_collaborators("ELETRICA", "/electrical/management/collaborators")

    async def load_instrumentation_collaborators(self):
        return await self._load_area_collaborators("INSTRUMENTACAO", "/instrumentation/management/collaborators")

    async def load_mechanical_collaborators(self):
        return await self._load_area_collaborators("MECANICA", "/mechanical/management/collaborators")

    async def load_electrical_report(self):
        return await self._load_area_report("ELETRICA", "/electrical/reports/monthly")

    async def load_instrumentation_report(self):
        return await self._load_area_report("INSTRUMENTACAO", "/instrumentation/reports/monthly")

    async def load_mechanical_report(self):
        return await self._load_area_report("MECANICA", "/mechanical/reports/monthly")

