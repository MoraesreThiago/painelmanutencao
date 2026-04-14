from __future__ import annotations

import reflex as rx

from components.common import (
    action_tile,
    alert_card,
    empty_state,
    metric_card,
    page_header,
    status_badge,
    surface_panel,
    table_panel,
)
from components.app_shell import app_shell
from states.app_state import AppState
from theme.theme import COLORS, RADII, TYPOGRAPHY


def _metric(item) -> rx.Component:
    return metric_card(item["label"], item["value"], tone=item["tone"])


def _alert(item) -> rx.Component:
    return alert_card(item["title"], item["description"], tone=item["tone"])


def _area_entry(item) -> rx.Component:
    return action_tile(item["label"], item["route"], caption="Entrar na area")


def dashboard_page() -> rx.Component:
    body = rx.vstack(
        page_header(
            "Visao consolidada da manutencao",
            "O dashboard foi redesenhado como um centro de controle tecnico, com leitura mais madura, densidade operacional e acesso rapido por area.",
            eyebrow_label="Control room",
        ),
        surface_panel(
            rx.flex(
                rx.vstack(
                    rx.hstack(
                        status_badge("FastAPI como fonte de verdade", tone="accent"),
                        status_badge("Permissoes sincronizadas", tone="info"),
                        status_badge("Reflex web frontend", tone="neutral"),
                        spacing="2",
                        wrap="wrap",
                    ),
                    rx.heading(
                        "Leitura executiva e operacional em um canvas unico.",
                        size="8",
                        color=COLORS["text"],
                        font_family=TYPOGRAPHY["display"],
                        letter_spacing="-0.05em",
                        max_width="14ch",
                    ),
                    rx.text(
                        "A experiencia visual agora prioriza foco, hierarquia forte e transicao rapida entre areas, sem duplicar regras do backend.",
                        color=COLORS["text_muted"],
                        font_size="1rem",
                        max_width="60ch",
                        line_height="1.8",
                    ),
                    spacing="4",
                    align="start",
                    flex="1",
                ),
                rx.box(
                    rx.vstack(
                        rx.text(
                            "Sessao atual",
                            color=COLORS["text_soft"],
                            font_size="0.74rem",
                            text_transform="uppercase",
                            letter_spacing="0.08em",
                            font_weight="800",
                        ),
                        rx.heading(AppState.current_user_name, size="5", font_family=TYPOGRAPHY["display"], color=COLORS["text"]),
                        rx.text(AppState.current_user_email, color=COLORS["text_muted"], font_size="0.92rem"),
                        rx.hstack(
                            status_badge(AppState.role_name, tone="info"),
                            rx.cond(
                                AppState.current_area_name != "",
                                status_badge(AppState.current_area_name, tone="accent"),
                                status_badge("Visao geral", tone="neutral"),
                            ),
                            spacing="2",
                            wrap="wrap",
                        ),
                        spacing="3",
                        align="start",
                        width="100%",
                    ),
                    min_width="280px",
                    max_width="320px",
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
            background=f"radial-gradient(circle at top right, {COLORS['accent_glow']} 0%, rgba(255,255,255,0) 36%), linear-gradient(180deg, #FFFFFF 0%, #F8FBFD 100%)",
        ),
        rx.cond(
            AppState.dashboard_error != "",
            empty_state("Erro ao carregar dashboard", AppState.dashboard_error),
            rx.vstack(
                rx.box(
                    rx.foreach(AppState.dashboard_metrics, _metric),
                    display="grid",
                    grid_template_columns="repeat(auto-fit, minmax(220px, 1fr))",
                    gap="1rem",
                    width="100%",
                ),
                rx.cond(
                    AppState.area_switcher_items.length() > 0,
                    surface_panel(
                        rx.vstack(
                            rx.hstack(
                                rx.heading("Acesso rapido por area", size="5", color=COLORS["text"], font_family=TYPOGRAPHY["display"]),
                                status_badge("Contextual", tone="accent"),
                                justify="between",
                                align="center",
                                width="100%",
                                wrap="wrap",
                            ),
                            rx.text(
                                "Entre direto no workspace operacional de cada area disponivel para a sua sessao.",
                                color=COLORS["text_muted"],
                                font_size="0.94rem",
                            ),
                            rx.box(
                                rx.foreach(AppState.area_switcher_items, _area_entry),
                                display="grid",
                                grid_template_columns="repeat(auto-fit, minmax(240px, 1fr))",
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
                rx.box(
                    surface_panel(
                        rx.vstack(
                            rx.hstack(
                                rx.heading("Prioridades do momento", size="5", color=COLORS["text"], font_family=TYPOGRAPHY["display"]),
                                status_badge("Leitura rapida", tone="warning"),
                                justify="between",
                                align="center",
                                width="100%",
                                wrap="wrap",
                            ),
                            rx.cond(
                                AppState.dashboard_alerts.length() > 0,
                                rx.vstack(rx.foreach(AppState.dashboard_alerts, _alert), spacing="3", width="100%"),
                                empty_state("Sem alertas ativos", "Nao ha alertas relevantes para o contexto atual."),
                            ),
                            spacing="4",
                            align="stretch",
                            width="100%",
                        )
                    ),
                    table_panel(
                        "Resumo por area",
                        ["Area", "Equipamentos", "Motores", "Instrumentos"],
                        AppState.dashboard_area_summary_rows,
                        "Consolidado sintetico para leitura gerencial e tecnica.",
                    ),
                    display="grid",
                    grid_template_columns="repeat(auto-fit, minmax(320px, 1fr))",
                    gap="1rem",
                    width="100%",
                ),
                table_panel(
                    "Movimentacoes recentes",
                    ["Equipamento", "Descricao", "Local", "Data", "Responsavel", "Motivo"],
                    AppState.dashboard_recent_movements_rows,
                    "Ultimos eventos de rastreabilidade registrados no sistema.",
                ),
                spacing="4",
                align="stretch",
                width="100%",
            ),
        ),
        spacing="5",
        width="100%",
        align="stretch",
    )
    return app_shell(body)

