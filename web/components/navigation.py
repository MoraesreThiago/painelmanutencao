from __future__ import annotations

import reflex as rx

from theme.theme import COLORS, RADII, TYPOGRAPHY


def _nav_link(item) -> rx.Component:
    return rx.link(
        rx.hstack(
            rx.box(
                width="4px",
                height="32px",
                border_radius=RADII["pill"],
                background=rx.cond(item["active"], COLORS["accent"], "transparent"),
                flex_shrink="0",
            ),
            rx.vstack(
                rx.text(
                    item["label"],
                    color=rx.cond(item["active"], "#FFFFFF", "#C7D2DD"),
                    font_weight=rx.cond(item["active"], "700", "600"),
                    font_family=TYPOGRAPHY["display"],
                    letter_spacing="-0.02em",
                ),
                rx.text(
                    "Navegacao operacional",
                    color=rx.cond(item["active"], "#8FD7E5", "#70859A"),
                    font_size="0.74rem",
                ),
                spacing="0",
                align="start",
                width="100%",
            ),
            justify="start",
            align="center",
            spacing="3",
            width="100%",
            padding="10px 12px",
            border_radius=RADII["md"],
            background=rx.cond(item["active"], "rgba(31, 163, 163, 0.14)", "transparent"),
            border=rx.cond(item["active"], f"1px solid {COLORS['accent']}44", "1px solid transparent"),
            transition="all 0.18s ease",
            _hover={"background": "rgba(255,255,255,0.05)"},
        ),
        href=item["route"],
        text_decoration="none",
        width="100%",
    )


def nav_group(title, items) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.text(
                title,
                color="#8EBCA5",
                font_size="0.72rem",
                text_transform="uppercase",
                letter_spacing="0.1em",
                font_weight="800",
            ),
            rx.foreach(items, _nav_link),
            spacing="2",
            width="100%",
            align="stretch",
        ),
        padding="14px",
        border_radius=RADII["md"],
        background="rgba(255,255,255,0.03)",
        border="1px solid rgba(255,255,255,0.05)",
        width="100%",
    )

