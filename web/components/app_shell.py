from __future__ import annotations

import reflex as rx

from components.common import brand_lockup, eyebrow, status_badge, surface_panel
from components.navigation import nav_group
from states.app_state import AppState
from theme.theme import COLORS, RADII, SPACE, TYPOGRAPHY


def _area_sections() -> rx.Component:
    return rx.cond(
        AppState.current_area_code == "ELETRICA",
        rx.vstack(
            rx.cond(AppState.electrical_principal_items.length() > 0, nav_group("Principal", AppState.electrical_principal_items), rx.fragment()),
            rx.cond(AppState.electrical_service_items.length() > 0, nav_group("Servicos", AppState.electrical_service_items), rx.fragment()),
            rx.cond(AppState.electrical_report_items.length() > 0, nav_group("Relatorios", AppState.electrical_report_items), rx.fragment()),
            rx.cond(AppState.electrical_management_items.length() > 0, nav_group("Gestao", AppState.electrical_management_items), rx.fragment()),
            spacing="3",
            width="100%",
            align="stretch",
        ),
        rx.cond(
            AppState.current_area_code == "INSTRUMENTACAO",
            rx.vstack(
                rx.cond(AppState.instrumentation_principal_items.length() > 0, nav_group("Principal", AppState.instrumentation_principal_items), rx.fragment()),
                rx.cond(AppState.instrumentation_service_items.length() > 0, nav_group("Servicos", AppState.instrumentation_service_items), rx.fragment()),
                rx.cond(AppState.instrumentation_report_items.length() > 0, nav_group("Relatorios", AppState.instrumentation_report_items), rx.fragment()),
                rx.cond(AppState.instrumentation_management_items.length() > 0, nav_group("Gestao", AppState.instrumentation_management_items), rx.fragment()),
                spacing="3",
                width="100%",
                align="stretch",
            ),
            rx.cond(
                AppState.current_area_code == "MECANICA",
                rx.vstack(
                    rx.cond(AppState.mechanical_principal_items.length() > 0, nav_group("Principal", AppState.mechanical_principal_items), rx.fragment()),
                    rx.cond(AppState.mechanical_service_items.length() > 0, nav_group("Servicos", AppState.mechanical_service_items), rx.fragment()),
                    rx.cond(AppState.mechanical_report_items.length() > 0, nav_group("Relatorios", AppState.mechanical_report_items), rx.fragment()),
                    rx.cond(AppState.mechanical_management_items.length() > 0, nav_group("Gestao", AppState.mechanical_management_items), rx.fragment()),
                    spacing="3",
                    width="100%",
                    align="stretch",
                ),
                rx.fragment(),
            ),
        ),
    )


def _brand_block() -> rx.Component:
    return rx.box(
        rx.vstack(
            brand_lockup(dark=True),
            rx.text(
                "Sistema institucional da Bem Brasil com leitura operacional de manutencao, rastreabilidade e controle tecnico.",
                color="#A7BBC9",
                font_size="0.9rem",
                line_height="1.7",
            ),
            rx.hstack(
                eyebrow("Bem Brasil", tone="brand"),
                status_badge("Painel industrial", tone="info"),
                status_badge("Produto B2B", tone="neutral"),
                spacing="2",
                wrap="wrap",
            ),
            spacing="3",
            align="start",
            width="100%",
        ),
        padding=SPACE["lg"],
        border_radius=RADII["lg"],
        background="linear-gradient(180deg, rgba(0,122,94,0.15) 0%, rgba(255,255,255,0.03) 100%)",
        border="1px solid rgba(0,122,94,0.20)",
        box_shadow="inset 0 1px 0 rgba(255,255,255,0.04)",
        width="100%",
    )


def _context_card() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.vstack(
                    rx.text(
                        "Contexto ativo",
                        color="#8EBCA5",
                        font_size="0.74rem",
                        text_transform="uppercase",
                        letter_spacing="0.08em",
                        font_weight="800",
                    ),
                    rx.heading(
                        rx.cond(AppState.current_area_name != "", AppState.current_area_name, "Visao consolidada"),
                        size="5",
                        color="#FFFFFF",
                        font_family=TYPOGRAPHY["display"],
                    ),
                    spacing="1",
                    align="start",
                ),
                status_badge(AppState.role_name, tone="brand"),
                justify="between",
                align="start",
                width="100%",
                wrap="wrap",
            ),
            rx.box(
                rx.box(
                    rx.text("Areas", color="#7F97AB", font_size="0.72rem", text_transform="uppercase", letter_spacing="0.08em", font_weight="700"),
                    rx.heading(AppState.allowed_areas.length(), size="6", color="#FFFFFF", font_family=TYPOGRAPHY["display"]),
                ),
                rx.box(
                    rx.text("Permissoes", color="#7F97AB", font_size="0.72rem", text_transform="uppercase", letter_spacing="0.08em", font_weight="700"),
                    rx.heading(AppState.permissions.length(), size="6", color="#FFFFFF", font_family=TYPOGRAPHY["display"]),
                ),
                display="grid",
                grid_template_columns="repeat(2, minmax(0, 1fr))",
                gap="0.9rem",
                width="100%",
            ),
            rx.text(
                "A navegacao muda de acordo com area, nivel e permissoes ja validadas no backend.",
                color="#9CB0C2",
                font_size="0.86rem",
                line_height="1.7",
            ),
            spacing="4",
            align="stretch",
            width="100%",
        ),
        padding=SPACE["lg"],
        border_radius=RADII["lg"],
        background="linear-gradient(180deg, rgba(10, 26, 37, 0.82) 0%, rgba(18, 48, 71, 0.95) 100%)",
        border="1px solid rgba(0,122,94,0.22)",
        box_shadow="0 0 0 1px rgba(0,122,94,0.05), 0 20px 42px rgba(0,122,94,0.12)",
        width="100%",
    )


def _session_panel() -> rx.Component:
    return surface_panel(
        rx.vstack(
            rx.vstack(
                rx.text(
                    "Sessao",
                    color=COLORS["text_soft"],
                    font_size="0.74rem",
                    text_transform="uppercase",
                    letter_spacing="0.08em",
                    font_weight="800",
                ),
                rx.heading(AppState.current_user_name, size="4", font_family=TYPOGRAPHY["display"], color=COLORS["text"]),
                rx.text(AppState.current_user_email, color=COLORS["text_muted"], font_size="0.86rem"),
                spacing="1",
                align="start",
                width="100%",
            ),
            rx.hstack(
                status_badge("Sistema online", tone="success"),
                rx.cond(
                    AppState.current_area_name != "",
                    status_badge(AppState.current_area_name, tone="info"),
                    status_badge("Multi-area", tone="neutral"),
                ),
                spacing="2",
                wrap="wrap",
            ),
            rx.button(
                "Encerrar sessao",
                on_click=AppState.logout,
                width="100%",
                background=COLORS["panel_alt"],
                color=COLORS["text"],
                border=f"1px solid {COLORS['border']}",
                border_radius=RADII["md"],
                font_weight="700",
                _hover={"background": COLORS["surface_alt"]},
            ),
            spacing="4",
            align="stretch",
            width="100%",
        ),
        padding=SPACE["md"],
        background="linear-gradient(180deg, #FFFFFF 0%, #F5F9FC 100%)",
    )


def app_shell(content: rx.Component) -> rx.Component:
    sidebar = rx.box(
        rx.vstack(
            _brand_block(),
            _context_card(),
            nav_group("Sistema", AppState.system_nav_items),
            nav_group("Areas", AppState.area_switcher_items),
            _area_sections(),
            rx.spacer(),
            _session_panel(),
            spacing="4",
            align="stretch",
            width="100%",
            height="100%",
        ),
        width="336px",
        min_width="336px",
        min_height="100vh",
        background=f"linear-gradient(180deg, {COLORS['sidebar']} 0%, {COLORS['sidebar_alt']} 100%)",
        padding=SPACE["xl"],
        border_right="1px solid rgba(255,255,255,0.05)",
        box_shadow="inset -1px 0 0 rgba(255,255,255,0.02)",
    )

    main_canvas = rx.box(
        content,
        flex="1",
        min_height="100vh",
        padding_x=SPACE["xl"],
        padding_top=SPACE["lg"],
        padding_bottom=SPACE["xl"],
        background=f"radial-gradient(circle at top right, rgba(0,122,94,0.08) 0%, rgba(255,255,255,0) 24%), radial-gradient(circle at top left, {COLORS['accent_glow']} 0%, rgba(255,255,255,0) 22%), linear-gradient(180deg, {COLORS['surface']} 0%, #F7FAFC 100%)",
    )

    return rx.box(
        rx.flex(
            sidebar,
            main_canvas,
            direction="row",
            wrap="wrap",
            width="100%",
            min_height="100vh",
        ),
        background=COLORS["surface"],
        min_height="100vh",
    )

