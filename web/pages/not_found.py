from __future__ import annotations

import reflex as rx

from components.common import page_header, surface_panel
from theme.theme import COLORS, SPACE


def not_found_page() -> rx.Component:
    return rx.center(
        surface_panel(
            rx.vstack(
                page_header(
                    "Pagina nao encontrada",
                    "O caminho que voce tentou abrir nao existe ou nao esta disponivel para o seu perfil.",
                    eyebrow_label=None,
                ),
                rx.hstack(
                    rx.link(
                        rx.button(
                            "Ir para login",
                            background=COLORS["brand"],
                            color="#FFFFFF",
                            border="none",
                            _hover={"background": COLORS["brand_alt"]},
                        ),
                        href="/login",
                        text_decoration="none",
                    ),
                    rx.link(
                        rx.button(
                            "Abrir dashboard",
                            variant="surface",
                        ),
                        href="/dashboard",
                        text_decoration="none",
                    ),
                    spacing="3",
                    wrap="wrap",
                ),
                spacing="4",
                align="start",
                width="100%",
            ),
            max_width="640px",
            padding=SPACE["xl"],
        ),
        min_height="100vh",
        width="100%",
        padding=SPACE["xl"],
        background=(
            f"radial-gradient(circle at top right, rgba(0,122,94,0.08) 0%, rgba(255,255,255,0) 26%), "
            f"radial-gradient(circle at top left, {COLORS['accent_glow']} 0%, rgba(255,255,255,0) 24%), "
            f"linear-gradient(180deg, {COLORS['surface']} 0%, #F7FAFC 100%)"
        ),
    )
