from __future__ import annotations

from typing import Any

import reflex as rx

from theme.theme import BRANDING, COLORS, RADII, SHADOWS, SPACE, TYPOGRAPHY


def eyebrow(label: Any, *, tone: str = "accent") -> rx.Component:
    tone_map = {
        "accent": (COLORS["accent_glow"], COLORS["accent_dark"]),
        "brand": (COLORS["brand_soft"], COLORS["brand"]),
        "info": (COLORS["electric_soft"], COLORS["electric"]),
        "warning": (COLORS["amber_soft"], COLORS["amber"]),
        "success": (COLORS["success_soft"], COLORS["success"]),
        "danger": (COLORS["danger_soft"], COLORS["danger"]),
        "neutral": (COLORS["panel_alt"], COLORS["text_muted"]),
    }
    background, color = tone_map.get(tone, tone_map["accent"])
    return rx.box(
        rx.text(
            label,
            font_size="0.74rem",
            font_weight="700",
            letter_spacing="0.08em",
            text_transform="uppercase",
            line_height="1",
        ),
        padding="7px 10px",
        border_radius=RADII["pill"],
        background=background,
        color=color,
        display="inline-flex",
        align_items="center",
        border=f"1px solid {color}22",
    )


def status_badge(label: Any, tone: str = "neutral") -> rx.Component:
    palette = {
        "neutral": (COLORS["panel_alt"], COLORS["text_muted"]),
        "accent": (COLORS["accent_soft"], COLORS["accent_dark"]),
        "brand": (COLORS["brand_soft"], COLORS["brand"]),
        "info": (COLORS["electric_soft"], COLORS["electric"]),
        "warning": (COLORS["amber_soft"], COLORS["amber"]),
        "danger": (COLORS["danger_soft"], COLORS["danger"]),
        "success": (COLORS["success_soft"], COLORS["success"]),
    }
    background, color = palette.get(tone, palette["neutral"])
    return rx.box(
        rx.text(label, font_size="0.82rem", font_weight="600", line_height="1"),
        padding="7px 12px",
        border_radius=RADII["pill"],
        background=background,
        color=color,
        display="inline-flex",
        align_items="center",
        border=f"1px solid {color}22",
    )


def page_header(title: Any, subtitle: Any, *, eyebrow_label: Any | None = "Operacao") -> rx.Component:
    return rx.vstack(
        rx.cond(
            eyebrow_label is not None,
            eyebrow(eyebrow_label, tone="accent"),
            rx.fragment(),
        ),
        rx.heading(
            title,
            size="8",
            color=COLORS["text"],
            font_family=TYPOGRAPHY["display"],
            letter_spacing="-0.03em",
        ),
        rx.text(
            subtitle,
            color=COLORS["text_muted"],
            font_size="1rem",
            max_width="68ch",
            line_height="1.7",
        ),
        spacing="2",
        align="start",
        width="100%",
    )


def brand_lockup(*, compact: bool = False, dark: bool = False, show_tagline: bool = True) -> rx.Component:
    primary_text = "#FFFFFF" if dark else COLORS["text"]
    secondary_text = "#A8BBCB" if dark else COLORS["text_soft"]
    brand_label = "#93B8A8" if dark else COLORS["brand"]
    return rx.hstack(
        rx.image(
            src="/bem-brasil-logo.png",
            alt="Bem Brasil",
            width="154px" if compact else "188px",
            height="auto",
            object_fit="contain",
            flex_shrink="0",
        ),
        rx.vstack(
            rx.text(
                BRANDING["app_name"],
                color=primary_text,
                font_family=TYPOGRAPHY["display"],
                font_weight="700",
                font_size="1.18rem" if compact else "1.4rem",
                letter_spacing="-0.03em",
            ),
            rx.hstack(
                rx.text(
                    BRANDING["app_subtitle"],
                    color=secondary_text,
                    font_size="0.8rem" if compact else "0.86rem",
                    letter_spacing="0.08em",
                    text_transform="uppercase",
                    font_weight="700",
                ),
                rx.cond(
                    show_tagline,
                    rx.text(
                        "por Bem Brasil",
                        color=brand_label,
                        font_size="0.8rem" if compact else "0.86rem",
                        font_weight="700",
                    ),
                    rx.fragment(),
                ),
                spacing="2",
                wrap="wrap",
            ),
            spacing="1",
            align="start",
        ),
        spacing="3",
        align="center",
        width="100%",
    )


def surface_panel(*children, **style) -> rx.Component:
    style.setdefault("background", COLORS["panel"])
    style.setdefault("border", f"1px solid {COLORS['border']}")
    style.setdefault("border_radius", RADII["lg"])
    style.setdefault("box_shadow", SHADOWS["panel"])
    style.setdefault("padding", SPACE["lg"])
    style.setdefault("width", "100%")
    return rx.box(*children, **style)


def soft_panel(*children, **style) -> rx.Component:
    style.setdefault("background", COLORS["panel_alt"])
    style.setdefault("border", f"1px solid {COLORS['chrome']}")
    style.setdefault("border_radius", RADII["md"])
    style.setdefault("padding", SPACE["lg"])
    style.setdefault("width", "100%")
    return rx.box(*children, **style)


def metric_card(label: Any, value: Any, *, tone: str = "accent", note: Any | None = None) -> rx.Component:
    tone_map = {
        "accent": (COLORS["accent"], COLORS["accent_glow"]),
        "info": (COLORS["electric"], COLORS["electric_soft"]),
        "warning": (COLORS["amber"], COLORS["amber_soft"]),
        "success": (COLORS["success"], COLORS["success_soft"]),
        "danger": (COLORS["danger"], COLORS["danger_soft"]),
    }
    line_color, wash = tone_map.get(tone, tone_map["accent"])
    return surface_panel(
        rx.vstack(
            rx.box(height="4px", width="64px", background=line_color, border_radius=RADII["pill"]),
            rx.text(label, color=COLORS["text_muted"], font_size="0.9rem", font_weight="600"),
            rx.heading(
                value,
                size="8",
                color=COLORS["text"],
                font_family=TYPOGRAPHY["display"],
                letter_spacing="-0.04em",
            ),
            rx.cond(
                note is not None,
                rx.text(note, color=COLORS["text_soft"], font_size="0.82rem"),
                rx.fragment(),
            ),
            spacing="2",
            align="start",
            width="100%",
        ),
        min_height="158px",
        background=f"linear-gradient(180deg, {COLORS['panel']} 0%, {wash} 180%)",
    )


def loading_state(message: Any = "Carregando dados do modulo...") -> rx.Component:
    return surface_panel(
        rx.center(
            rx.vstack(
                rx.spinner(color=COLORS["accent"], size="3"),
                rx.text(message, color=COLORS["text_muted"], font_size="0.96rem"),
                spacing="3",
                align="center",
            ),
            min_height="220px",
        )
    )


def empty_state(title: Any, description: Any) -> rx.Component:
    return surface_panel(
        rx.vstack(
            eyebrow("Sem registros", tone="neutral"),
            rx.heading(title, size="5", color=COLORS["text"], font_family=TYPOGRAPHY["display"]),
            rx.text(description, color=COLORS["text_muted"], line_height="1.7"),
            spacing="3",
            align="start",
        ),
        border_style="dashed",
        border_color=COLORS["border_strong"],
        background="linear-gradient(180deg, #FFFFFF 0%, #F8FBFD 100%)",
    )


def action_tile(label: Any, href: Any, *, caption: Any = "Abrir modulo") -> rx.Component:
    return rx.link(
        surface_panel(
            rx.vstack(
                rx.text(
                    caption,
                    color=COLORS["text_soft"],
                    font_size="0.76rem",
                    text_transform="uppercase",
                    letter_spacing="0.08em",
                    font_weight="700",
                ),
                rx.hstack(
                    rx.heading(label, size="4", color=COLORS["text"], font_family=TYPOGRAPHY["display"]),
                    rx.text("->", color=COLORS["accent_dark"], font_size="1rem", font_weight="700"),
                    justify="between",
                    align="center",
                    width="100%",
                ),
                rx.text(
                    "Acesso rapido para o contexto atual.",
                    color=COLORS["text_muted"],
                    font_size="0.88rem",
                ),
                spacing="2",
                align="start",
                width="100%",
            ),
            padding=SPACE["md"],
            _hover={
                "border_color": COLORS["accent"],
                "box_shadow": SHADOWS["glow"],
                "transform": "translateY(-2px)",
            },
            transition="all 0.18s ease",
        ),
        href=href,
        text_decoration="none",
        width="100%",
    )


def action_link(label: Any, href: Any, *, caption: Any = "Abrir modulo") -> rx.Component:
    return action_tile(label, href, caption=caption)


def alert_card(title: Any, description: Any, *, tone: str = "warning") -> rx.Component:
    return soft_panel(
        rx.vstack(
            status_badge(tone.title(), tone=tone),
            rx.heading(title, size="4", color=COLORS["text"], font_family=TYPOGRAPHY["display"]),
            rx.text(description, color=COLORS["text_muted"], font_size="0.92rem", line_height="1.7"),
            spacing="2",
            align="start",
            width="100%",
        )
    )


def section_block(title: Any, description: Any | None = None, *children) -> rx.Component:
    return surface_panel(
        rx.vstack(
            rx.vstack(
                rx.heading(title, size="5", color=COLORS["text"], font_family=TYPOGRAPHY["display"]),
                rx.cond(
                    description is not None,
                    rx.text(description, color=COLORS["text_muted"], font_size="0.92rem"),
                    rx.fragment(),
                ),
                spacing="1",
                align="start",
                width="100%",
            ),
            *children,
            spacing="4",
            align="stretch",
            width="100%",
        )
    )


def table_panel(title: Any, columns: Any, rows: Any, description: Any | None = None) -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.heading(title, size="5", color=COLORS["text"], font_family=TYPOGRAPHY["display"]),
            status_badge("Dados ativos", tone="neutral"),
            justify="between",
            align="center",
            width="100%",
            wrap="wrap",
        ),
        rx.cond(
            rows.length() > 0,
            surface_panel(
                rx.vstack(
                    rx.cond(
                        description is not None,
                        rx.text(description, color=COLORS["text_muted"], font_size="0.92rem"),
                        rx.fragment(),
                    ),
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.foreach(
                                    columns,
                                    lambda column: rx.table.column_header_cell(
                                        column,
                                        color=COLORS["text_soft"],
                                        font_size="0.76rem",
                                        text_transform="uppercase",
                                        letter_spacing="0.08em",
                                        font_weight="700",
                                    ),
                                )
                            )
                        ),
                        rx.table.body(
                            rx.foreach(
                                rows,
                                lambda row: rx.table.row(
                                    rx.foreach(
                                        row,
                                        lambda cell: rx.table.cell(
                                            cell,
                                            color=COLORS["text"],
                                            font_size="0.92rem",
                                            vertical_align="top",
                                        ),
                                    )
                                ),
                            )
                        ),
                        variant="surface",
                        size="2",
                        width="100%",
                    ),
                    spacing="4",
                    width="100%",
                    align="stretch",
                ),
                background="linear-gradient(180deg, #FFFFFF 0%, #FAFCFD 100%)",
            ),
            empty_state("Sem registros", "Nenhum item disponivel para o contexto atual."),
        ),
        spacing="3",
        width="100%",
        align="stretch",
    )

