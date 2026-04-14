from __future__ import annotations

from typing import Any

import reflex as rx

from components.common import surface_panel
from pages.auth.config import INPUT_STYLE, LoginView
from states.app_state import AppState
from theme.theme import COLORS, RADII, SHADOWS, SPACE, TYPOGRAPHY


def ambient_glow(
    *,
    background: str,
    width: str,
    height: str,
    top: str | None = None,
    left: str | None = None,
    bottom: str | None = None,
    right: str | None = None,
) -> rx.Component:
    return rx.box(
        background=background,
        width=width,
        height=height,
        border_radius=RADII["pill"],
        position="absolute",
        top=top,
        left=left,
        bottom=bottom,
        right=right,
    )


def background_canvas(view: LoginView) -> rx.Component:
    return rx.box(
        ambient_glow(
            background=view.primary_glow,
            width="540px",
            height="540px",
            top="-120px",
            left="-120px",
        ),
        ambient_glow(
            background=view.secondary_glow,
            width="620px",
            height="620px",
            bottom="-180px",
            right="-160px",
        ),
        rx.box(
            rx.image(
                src="/bem-brasil-logo.png",
                alt="Bem Brasil",
                width="720px",
                height="auto",
                object_fit="contain",
                opacity=view.logo_opacity,
                filter=view.logo_filter,
            ),
            position="absolute",
            inset="0",
            display="flex",
            align_items="center",
            justify_content="center",
            pointer_events="none",
        ),
        position="absolute",
        inset="0",
        overflow="hidden",
        pointer_events="none",
    )


def brand_header(view: LoginView) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.heading(
                view.title,
                size="7",
                color=COLORS["text"],
                font_family=TYPOGRAPHY["display"],
                letter_spacing="-0.04em",
                line_height="1",
            ),
            spacing="3",
            align="start",
            width="100%",
        ),
        width="100%",
        min_height="44px",
        display="flex",
        align_items="center",
        padding_bottom="2px",
    )


def credential_field(
    *,
    label: str,
    name: str,
    input_type: str,
    placeholder: str,
    default_value: Any,
    spell_check: bool | None = None,
) -> rx.Component:
    input_props = dict(INPUT_STYLE)
    input_props.update(
        {
            "name": name,
            "default_value": default_value,
            "type": input_type,
            "placeholder": placeholder,
        }
    )
    if spell_check is not None:
        input_props["spell_check"] = spell_check

    return rx.vstack(
        rx.text(
            label,
            font_size="1rem",
            font_weight="800",
            color=COLORS["text"],
        ),
        rx.input(
            **input_props,
            disabled=AppState.login_loading,
        ),
        spacing="2",
        width="100%",
        align="start",
    )


def auth_error() -> rx.Component:
    return rx.cond(
        AppState.auth_error != "",
        rx.box(
            rx.text(AppState.auth_error, color=COLORS["danger"], font_weight="600"),
            width="100%",
            padding="12px 14px",
            border_radius=RADII["md"],
            background=COLORS["danger_soft"],
            border=f"1px solid {COLORS['danger']}33",
        ),
        rx.fragment(),
    )


def remember_me_field() -> rx.Component:
    return rx.box(
        rx.checkbox(
            "Lembrar de mim",
            name="remember_me",
            value="true",
            default_checked=AppState.remember_me_enabled,
            color_scheme="green",
            size="2",
            disabled=AppState.login_loading,
        ),
        width="100%",
        display="flex",
        align_items="center",
        justify_content="flex-start",
        padding_top="2px",
    )


def submit_button() -> rx.Component:
    return rx.button(
        rx.hstack(
            rx.cond(
                AppState.login_loading,
                rx.spinner(size="2", color="#FFFFFF"),
                rx.fragment(),
            ),
            rx.text(
                rx.cond(AppState.login_loading, "Entrando...", "Entrar"),
                color="#FFFFFF",
                font_weight="800",
                line_height="1",
            ),
            spacing="2",
            align="center",
            justify="center",
            width="100%",
        ),
        type="submit",
        width="100%",
        min_height="50px",
        padding="0.92rem 1.2rem",
        border_radius=RADII["sm"],
        border="none",
        background=COLORS["brand"],
        box_shadow="0 10px 24px rgba(0, 122, 94, 0.20)",
        disabled=AppState.login_loading,
        _hover={"background": COLORS["brand_alt"]},
        _disabled={
            "background": COLORS["brand_alt"],
            "opacity": "0.92",
            "cursor": "not-allowed",
            "box_shadow": "0 10px 24px rgba(0, 122, 94, 0.14)",
        },
        transition="all 0.18s ease",
    )


def login_form() -> rx.Component:
    return rx.form(
        rx.vstack(
            credential_field(
                label="E-mail",
                name="email",
                input_type="email",
                placeholder="admin@maintenance.example.com",
                default_value=AppState.email,
                spell_check=False,
            ),
            credential_field(
                label="Senha",
                name="password",
                input_type="password",
                placeholder="Sua senha",
                default_value=AppState.password,
            ),
            auth_error(),
            remember_me_field(),
            submit_button(),
            spacing="3",
            align="stretch",
            width="100%",
        ),
        on_submit=AppState.submit_login_form,
        reset_on_submit=False,
        width="100%",
        auto_complete="off",
    )


def login_card(view: LoginView) -> rx.Component:
    return surface_panel(
        rx.vstack(
            brand_header(view),
            login_form(),
            rx.center(
                rx.image(
                    src="/bem-brasil-logo.png",
                    alt="Bem Brasil",
                    width="128px",
                    height="auto",
                    object_fit="contain",
                ),
                width="100%",
                min_height="40px",
                padding_top="6px",
            ),
            spacing="3",
            align="stretch",
            width="100%",
        ),
        max_width="528px",
        padding="28px 30px 22px 30px",
        background="linear-gradient(180deg, rgba(255,255,255,0.98) 0%, rgba(247,250,252,0.96) 100%)",
        border=f"1px solid {COLORS['chrome']}",
        box_shadow=SHADOWS["soft"],
        position="relative",
        z_index="2",
    )

