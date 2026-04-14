from __future__ import annotations

import reflex as rx

from pages.auth import electrical_login_page, login_page
from pages.dashboard import dashboard_page
from pages.module_page import module_page
from pages.not_found import not_found_page
from states.app_state import AppState
from theme.theme import BRANDING, GLOBAL_STYLE, app_theme


APP_IMAGE = "bem-brasil-logo.png"


def root_page() -> rx.Component:
    return rx.box(min_height="100vh")


app = rx.App(
    theme=app_theme(),
    style=GLOBAL_STYLE,
    stylesheets=[
        "https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap",
        "/theme.css",
    ],
    head_components=[
        rx.el.link(rel="icon", href=f"/{APP_IMAGE}"),
        rx.el.meta(name="theme-color", content="#123047"),
    ],
)

app.add_page(root_page, route="/", on_load=AppState.load_root, title=BRANDING["app_name"], image=APP_IMAGE)
app.add_page(login_page, route="/login", on_load=AppState.load_login_page, title=f"{BRANDING['app_name']} | Login", image=APP_IMAGE)
app.add_page(electrical_login_page, route="/login/electrical", on_load=AppState.load_electrical_login_page, title=f"{BRANDING['app_name']} | Login | Eletrica", image=APP_IMAGE)
app.add_page(not_found_page, route="404", title=f"{BRANDING['app_name']} | 404", image=APP_IMAGE)
app.add_page(dashboard_page, route="/dashboard", on_load=AppState.load_dashboard_page, title=f"{BRANDING['app_name']} | Dashboard", image=APP_IMAGE)

app.add_page(module_page, route="/electrical", on_load=AppState.load_electrical_home, title=f"{BRANDING['app_name']} | Eletrica", image=APP_IMAGE)
app.add_page(module_page, route="/electrical/occurrences", on_load=AppState.load_electrical_occurrences, title=f"{BRANDING['app_name']} | Eletrica | Ocorrencias", image=APP_IMAGE)
app.add_page(module_page, route="/electrical/history", on_load=AppState.load_electrical_history, title=f"{BRANDING['app_name']} | Eletrica | Historico", image=APP_IMAGE)
app.add_page(module_page, route="/electrical/equipments", on_load=AppState.load_electrical_equipments, title=f"{BRANDING['app_name']} | Eletrica | Equipamentos", image=APP_IMAGE)
app.add_page(module_page, route="/electrical/service-orders", on_load=AppState.load_electrical_service_orders, title=f"{BRANDING['app_name']} | Eletrica | Ordem de servico", image=APP_IMAGE)
app.add_page(module_page, route="/electrical/services/motors", on_load=AppState.load_electrical_services, title=f"{BRANDING['app_name']} | Eletrica | Motores", image=APP_IMAGE)
app.add_page(module_page, route="/electrical/reports/monthly", on_load=AppState.load_electrical_report, title=f"{BRANDING['app_name']} | Eletrica | Relatorio mensal", image=APP_IMAGE)
app.add_page(module_page, route="/electrical/management/collaborators", on_load=AppState.load_electrical_collaborators, title=f"{BRANDING['app_name']} | Eletrica | Colaboradores", image=APP_IMAGE)

app.add_page(module_page, route="/instrumentation", on_load=AppState.load_instrumentation_home, title=f"{BRANDING['app_name']} | Instrumentacao", image=APP_IMAGE)
app.add_page(module_page, route="/instrumentation/occurrences", on_load=AppState.load_instrumentation_occurrences, title=f"{BRANDING['app_name']} | Instrumentacao | Ocorrencias", image=APP_IMAGE)
app.add_page(module_page, route="/instrumentation/history", on_load=AppState.load_instrumentation_history, title=f"{BRANDING['app_name']} | Instrumentacao | Historico", image=APP_IMAGE)
app.add_page(module_page, route="/instrumentation/equipments", on_load=AppState.load_instrumentation_equipments, title=f"{BRANDING['app_name']} | Instrumentacao | Equipamentos", image=APP_IMAGE)
app.add_page(module_page, route="/instrumentation/services/instruments", on_load=AppState.load_instrumentation_services, title=f"{BRANDING['app_name']} | Instrumentacao | Instrumentos", image=APP_IMAGE)
app.add_page(module_page, route="/instrumentation/reports/monthly", on_load=AppState.load_instrumentation_report, title=f"{BRANDING['app_name']} | Instrumentacao | Relatorio mensal", image=APP_IMAGE)
app.add_page(module_page, route="/instrumentation/management/collaborators", on_load=AppState.load_instrumentation_collaborators, title=f"{BRANDING['app_name']} | Instrumentacao | Colaboradores", image=APP_IMAGE)

app.add_page(module_page, route="/mechanical", on_load=AppState.load_mechanical_home, title=f"{BRANDING['app_name']} | Mecanica", image=APP_IMAGE)
app.add_page(module_page, route="/mechanical/occurrences", on_load=AppState.load_mechanical_occurrences, title=f"{BRANDING['app_name']} | Mecanica | Ocorrencias", image=APP_IMAGE)
app.add_page(module_page, route="/mechanical/history", on_load=AppState.load_mechanical_history, title=f"{BRANDING['app_name']} | Mecanica | Historico", image=APP_IMAGE)
app.add_page(module_page, route="/mechanical/equipments", on_load=AppState.load_mechanical_equipments, title=f"{BRANDING['app_name']} | Mecanica | Equipamentos", image=APP_IMAGE)
app.add_page(module_page, route="/mechanical/reports/monthly", on_load=AppState.load_mechanical_report, title=f"{BRANDING['app_name']} | Mecanica | Relatorio mensal", image=APP_IMAGE)
app.add_page(module_page, route="/mechanical/management/collaborators", on_load=AppState.load_mechanical_collaborators, title=f"{BRANDING['app_name']} | Mecanica | Colaboradores", image=APP_IMAGE)
