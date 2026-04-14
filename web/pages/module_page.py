from __future__ import annotations

import reflex as rx

from components.common import (
    action_tile,
    alert_card,
    empty_state,
    loading_state,
    metric_card,
    page_header,
    status_badge,
    surface_panel,
    table_panel,
)
from components.workspace_shell import workspace_shell
from states.app_state import AppState
from theme.theme import COLORS, RADII, TYPOGRAPHY


def _metric(item) -> rx.Component:
    return metric_card(item["label"], item["value"], tone=item["tone"])


def _badge(item) -> rx.Component:
    return status_badge(item["label"], tone=item["tone"])


def _quick_link(item) -> rx.Component:
    return action_tile(item["label"], item["route"], caption="Abrir rota")


def _alert(item) -> rx.Component:
    return alert_card(item["title"], item["description"], tone=item["tone"])


def module_page() -> rx.Component:
    hero = surface_panel(
        rx.flex(
            rx.vstack(
                rx.hstack(rx.foreach(AppState.scope_badges, _badge), spacing="2", wrap="wrap"),
                rx.heading(
                    AppState.hero_title,
                    size="8",
                    color=COLORS["text"],
                    font_family=TYPOGRAPHY["display"],
                    letter_spacing="-0.05em",
                    max_width="15ch",
                ),
                rx.text(
                    AppState.hero_description,
                    color=COLORS["text_muted"],
                    font_size="1rem",
                    max_width="60ch",
                    line_height="1.8",
                ),
                rx.cond(
                    AppState.support_text != "",
                    rx.text(
                        AppState.support_text,
                        color=COLORS["text_soft"],
                        font_size="0.92rem",
                        max_width="68ch",
                        line_height="1.8",
                    ),
                    rx.fragment(),
                ),
                spacing="4",
                align="start",
                flex="1",
            ),
            rx.box(
                rx.vstack(
                    rx.text(
                        "Leitura do modulo",
                        color=COLORS["text_soft"],
                        font_size="0.74rem",
                        text_transform="uppercase",
                        letter_spacing="0.08em",
                        font_weight="800",
                    ),
                    rx.heading(
                        AppState.page_title,
                        size="5",
                        color=COLORS["text"],
                        font_family=TYPOGRAPHY["display"],
                    ),
                    rx.text(
                        AppState.page_subtitle,
                        color=COLORS["text_muted"],
                        font_size="0.92rem",
                        line_height="1.7",
                    ),
                    rx.hstack(
                        status_badge("Backend preservado", tone="info"),
                        status_badge("UI Reflex", tone="accent"),
                        spacing="2",
                        wrap="wrap",
                    ),
                    spacing="3",
                    align="start",
                    width="100%",
                ),
                min_width="280px",
                max_width="340px",
                padding="22px",
                border_radius=RADII["md"],
                background="linear-gradient(180deg, #FFFFFF 0%, #F2F7FB 100%)",
                border=f"1px solid {COLORS['chrome']}",
            ),
            justify="between",
            align="stretch",
            wrap="wrap",
            gap="1rem",
            width="100%",
        ),
        background=f"radial-gradient(circle at top right, {COLORS['accent_glow']} 0%, rgba(255,255,255,0) 34%), linear-gradient(180deg, #FFFFFF 0%, #F8FBFD 100%)",
    )

    body = rx.cond(
        AppState.page_loading,
        loading_state("Carregando o modulo com base nos dados atuais da API..."),
        rx.cond(
            AppState.page_error != "",
            empty_state("Nao foi possivel carregar esta pagina", AppState.page_error),
            rx.vstack(
                hero,
                rx.cond(
                    AppState.metric_cards.length() > 0,
                    rx.box(
                        rx.foreach(AppState.metric_cards, _metric),
                        display="grid",
                        grid_template_columns="repeat(auto-fit, minmax(220px, 1fr))",
                        gap="1rem",
                        width="100%",
                    ),
                    rx.fragment(),
                ),
                rx.cond(
                    AppState.quick_links.length() > 0,
                    surface_panel(
                        rx.vstack(
                            rx.hstack(
                                rx.heading("Rotas relacionadas", size="5", color=COLORS["text"], font_family=TYPOGRAPHY["display"]),
                                status_badge("Navegacao contextual", tone="neutral"),
                                justify="between",
                                align="center",
                                width="100%",
                                wrap="wrap",
                            ),
                            rx.text(
                                "Use os atalhos abaixo para navegar pelo modulo sem perder o contexto atual de area e permissao.",
                                color=COLORS["text_muted"],
                                font_size="0.94rem",
                            ),
                            rx.box(
                                rx.foreach(AppState.quick_links, _quick_link),
                                display="grid",
                                grid_template_columns="repeat(auto-fit, minmax(240px, 1fr))",
                                gap="1rem",
                                width="100%",
                            ),
                            spacing="4",
                            width="100%",
                            align="stretch",
                        )
                    ),
                    rx.fragment(),
                ),
                rx.cond(
                    AppState.alert_cards.length() > 0,
                    surface_panel(
                        rx.vstack(
                            rx.hstack(
                                rx.heading("Alertas e foco operacional", size="5", color=COLORS["text"], font_family=TYPOGRAPHY["display"]),
                                status_badge("Prioridades", tone="warning"),
                                justify="between",
                                align="center",
                                width="100%",
                                wrap="wrap",
                            ),
                            rx.box(
                                rx.foreach(AppState.alert_cards, _alert),
                                display="grid",
                                grid_template_columns="repeat(auto-fit, minmax(280px, 1fr))",
                                gap="1rem",
                                width="100%",
                            ),
                            spacing="4",
                            align="stretch",
                            width="100%",
                        )
                    ),
                    rx.fragment(),
                ),
                rx.cond(
                    AppState.primary_table_title != "",
                    table_panel(AppState.primary_table_title, AppState.primary_table_columns, AppState.primary_table_rows),
                    rx.fragment(),
                ),
                rx.cond(
                    AppState.secondary_table_title != "",
                    table_panel(AppState.secondary_table_title, AppState.secondary_table_columns, AppState.secondary_table_rows),
                    rx.fragment(),
                ),
                rx.cond(
                    AppState.tertiary_table_title != "",
                    table_panel(AppState.tertiary_table_title, AppState.tertiary_table_columns, AppState.tertiary_table_rows),
                    rx.fragment(),
                ),
                spacing="5",
                width="100%",
                align="stretch",
            ),
        ),
    )

    return workspace_shell(
        rx.vstack(
            page_header(AppState.page_title, AppState.page_subtitle, eyebrow_label=None),
            body,
            spacing="4",
            width="100%",
            align="stretch",
        )
    )

