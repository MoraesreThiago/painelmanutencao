from __future__ import annotations

import reflex as rx

from pages.auth.components import background_canvas, login_card
from pages.auth.config import DEFAULT_LOGIN_VIEW, ELECTRICAL_LOGIN_VIEW, LoginView
from theme.theme import COLORS, SPACE


def _build_login_page(view: LoginView) -> rx.Component:
    return rx.box(
        background_canvas(view),
        rx.box(
            login_card(view),
            width="100%",
            max_width="580px",
            margin="0 auto",
            padding_x="24px",
            padding_y="20px",
            display="flex",
            align_items="center",
            justify_content="center",
        ),
        position="relative",
        background=f"linear-gradient(160deg, {COLORS['bg']} 0%, {COLORS['bg_alt']} 100%)",
        min_height="100vh",
        overflow="hidden",
        display="flex",
        align_items="center",
        justify_content="center",
    )


def login_page() -> rx.Component:
    return _build_login_page(DEFAULT_LOGIN_VIEW)


def electrical_login_page() -> rx.Component:
    return _build_login_page(ELECTRICAL_LOGIN_VIEW)

