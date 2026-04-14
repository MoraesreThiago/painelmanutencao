from __future__ import annotations

import reflex as rx

from states.app_state import AppState
from theme.theme import COLORS, RADII, SPACE, TYPOGRAPHY


SIDEBAR_INNER_WIDTH = "220px"


def _menu_section_title(title: str) -> rx.Component:
    return rx.text(
        title,
        color="#7FA994",
        font_size="0.68rem",
        text_transform="uppercase",
        letter_spacing="0.09em",
        font_weight="800",
        padding_bottom="2px",
    )


def _sidebar_toggle_button() -> rx.Component:
    return rx.button(
        rx.cond(
            AppState.sidebar_collapsed,
            rx.icon("chevron_right", size=16, color=COLORS["sidebar"]),
            rx.icon("chevron_left", size=16, color=COLORS["sidebar"]),
        ),
        on_click=AppState.toggle_sidebar,
        width="34px",
        height="64px",
        min_width="34px",
        padding="0",
        border_radius=RADII["pill"],
        background="linear-gradient(180deg, #FFFFFF 0%, #EEF3F7 100%)",
        border="1px solid rgba(18,48,71,0.12)",
        box_shadow="0 10px 22px rgba(8,16,24,0.14), inset 0 1px 0 rgba(255,255,255,0.9)",
        _hover={
            "background": "linear-gradient(180deg, #FFFFFF 0%, #E7EEF4 100%)",
            "box_shadow": "0 12px 24px rgba(8,16,24,0.16), inset 0 1px 0 rgba(255,255,255,0.95)",
        },
        transition="background 0.18s ease, box-shadow 0.18s ease, transform 0.18s ease",
        title=rx.cond(AppState.sidebar_collapsed, "Expandir menu", "Minimizar menu"),
    )


def _sidebar_toggle_handle() -> rx.Component:
    return rx.center(
        rx.box(
            width="1px",
            height="84px",
            background="linear-gradient(180deg, rgba(255,255,255,0) 0%, rgba(18,48,71,0.14) 18%, rgba(18,48,71,0.14) 82%, rgba(255,255,255,0) 100%)",
        ),
        _sidebar_toggle_button(),
        position="absolute",
        top="50%",
        right="-18px",
        transform="translateY(-50%)",
        z_index="20",
        gap="0",
        pointer_events="auto",
    )


def _menu_icon(item) -> rx.Component:
    color = rx.cond(item["active"], "#A6E8D0", "#95A7B8")
    return rx.cond(
        item["label"] == "Painel Principal",
        rx.icon("house", size=16, color=color, flex_shrink="0"),
        rx.cond(
            item["label"] == "Ocorrências",
            rx.icon("triangle_alert", size=16, color=color, flex_shrink="0"),
            rx.cond(
                item["label"] == "Histórico",
                rx.icon("history", size=16, color=color, flex_shrink="0"),
                rx.cond(
                    item["label"] == "Equipamentos",
                    rx.icon("package", size=16, color=color, flex_shrink="0"),
                    rx.cond(
                        item["label"] == "Motores Elétricos",
                        rx.icon("bolt", size=16, color=color, flex_shrink="0"),
                        rx.icon("file_text", size=16, color=color, flex_shrink="0"),
                    ),
                ),
            ),
        ),
    )


def _expanded_workspace_nav_item_content(item) -> rx.Component:
    return rx.hstack(
        _menu_icon(item),
        rx.text(
            item["label"],
            color=rx.cond(item["active"], "#FFFFFF", "#D5DEE7"),
            font_family=TYPOGRAPHY["display"],
            font_weight=rx.cond(item["active"], "700", "600"),
            font_size="0.89rem",
            letter_spacing="-0.02em",
            line_height="1.15",
            flex="1",
            min_width="0",
        ),
        rx.icon(
            "chevron_right",
            size=14,
            color=rx.cond(item["active"], "#A6E8D0", "#7C90A2"),
            flex_shrink="0",
        ),
        align="center",
        spacing="2",
        width="100%",
        min_height="34px",
        padding="6px 10px",
        border_radius=RADII["sm"],
        background=rx.cond(item["active"], "rgba(255,255,255,0.08)", "transparent"),
        border=rx.cond(item["active"], "1px solid rgba(255,255,255,0.06)", "1px solid transparent"),
        box_shadow=rx.cond(
            item["active"],
            f"inset 3px 0 0 {COLORS['brand']}, inset 0 1px 0 rgba(255,255,255,0.04)",
            "none",
        ),
        transition="background 0.18s ease, color 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease",
        _hover={
            "background": "rgba(255,255,255,0.05)",
            "border_color": "rgba(255,255,255,0.04)",
        },
    )


def _collapsed_workspace_nav_item_content(item) -> rx.Component:
    return rx.center(
        _menu_icon(item),
        width="100%",
        min_height="40px",
        padding="7px 0",
        border_radius=RADII["sm"],
        background=rx.cond(item["active"], "rgba(255,255,255,0.08)", "transparent"),
        border=rx.cond(item["active"], "1px solid rgba(255,255,255,0.06)", "1px solid transparent"),
        box_shadow=rx.cond(
            item["active"],
            f"inset 3px 0 0 {COLORS['brand']}, inset 0 1px 0 rgba(255,255,255,0.04)",
            "none",
        ),
        transition="background 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease",
        _hover={
            "background": "rgba(255,255,255,0.05)",
            "border_color": "rgba(255,255,255,0.04)",
        },
    )


def _workspace_nav_item_content(item) -> rx.Component:
    return rx.cond(
        AppState.sidebar_collapsed,
        _collapsed_workspace_nav_item_content(item),
        _expanded_workspace_nav_item_content(item),
    )


def _workspace_nav_item(item) -> rx.Component:
    return rx.box(
        rx.link(
            _workspace_nav_item_content(item),
            href=item["route"],
            text_decoration="none",
            width="100%",
            title=item["label"],
        ),
        width="100%",
    )


def _sidebar_brand() -> rx.Component:
    return rx.box(
        rx.cond(
            AppState.sidebar_collapsed,
            rx.vstack(
                rx.center(
                    rx.image(
                        src="/bem-brasil-logo.png",
                        alt="Bem Brasil",
                        width="58px",
                        height="auto",
                        object_fit="contain",
                    ),
                    width="100%",
                ),
                rx.box(
                    width="100%",
                    height="1px",
                    background="linear-gradient(90deg, rgba(0,122,94,0.22) 0%, rgba(255,255,255,0.04) 100%)",
                ),
                spacing="3",
                align="stretch",
            ),
            rx.vstack(
                rx.hstack(
                    rx.image(
                        src="/bem-brasil-logo.png",
                        alt="Bem Brasil",
                        width="108px",
                        height="auto",
                        object_fit="contain",
                        flex_shrink="0",
                    ),
                    rx.vstack(
                        rx.text(
                            "Painel",
                            color="#D9E3EB",
                            font_family=TYPOGRAPHY["display"],
                            font_weight="600",
                            font_size="0.99rem",
                            letter_spacing="-0.02em",
                            line_height="1.05",
                        ),
                        rx.text(
                            "Manutenção",
                            color="#FFFFFF",
                            font_family=TYPOGRAPHY["display"],
                            font_weight="700",
                            font_size="1.1rem",
                            letter_spacing="-0.03em",
                            line_height="1.05",
                        ),
                        spacing="1",
                        align="start",
                        min_width="0",
                        max_width="100%",
                    ),
                    spacing="3",
                    align="center",
                    width="100%",
                ),
                rx.box(
                    width="100%",
                    height="1px",
                    background="linear-gradient(90deg, rgba(0,122,94,0.38) 0%, rgba(255,255,255,0.06) 100%)",
                ),
                spacing="3",
                align="stretch",
            ),
        ),
        width="100%",
        padding_top="2px",
        padding_bottom=SPACE["sm"],
        transition="all 0.22s ease",
    )


def _menu_section(title: str, items) -> rx.Component:
    return rx.vstack(
        rx.cond(
            AppState.sidebar_collapsed,
            rx.fragment(),
            _menu_section_title(title),
        ),
        rx.foreach(items, _workspace_nav_item),
        spacing=rx.cond(AppState.sidebar_collapsed, "1", "2"),
        width="100%",
        align=rx.cond(AppState.sidebar_collapsed, "center", "stretch"),
    )


def _menu_block() -> rx.Component:
    return rx.vstack(
        rx.cond(
            AppState.workspace_principal_items.length() > 0,
            _menu_section("Principal", AppState.workspace_principal_items),
            rx.fragment(),
        ),
        rx.cond(
            AppState.workspace_service_items.length() > 0,
            _menu_section("Serviços", AppState.workspace_service_items),
            rx.fragment(),
        ),
        rx.cond(
            AppState.workspace_report_items.length() > 0,
            _menu_section("Relatórios", AppState.workspace_report_items),
            rx.fragment(),
        ),
        width="100%",
        spacing=rx.cond(AppState.sidebar_collapsed, "4", "5"),
        align=rx.cond(AppState.sidebar_collapsed, "center", "stretch"),
    )


def _expanded_session_footer() -> rx.Component:
    trigger = rx.button(
        rx.hstack(
            rx.center(
                rx.text(
                    AppState.profile_initials,
                    color="#EAF4FA",
                    font_family=TYPOGRAPHY["display"],
                    font_weight="700",
                    font_size="0.78rem",
                    letter_spacing="0.02em",
                ),
                width="33px",
                height="33px",
                border_radius="999px",
                background="linear-gradient(180deg, rgba(255,255,255,0.10) 0%, rgba(255,255,255,0.06) 100%)",
                border="1px solid rgba(255,255,255,0.06)",
                flex_shrink="0",
            ),
            rx.text(
                AppState.profile_display_name,
                color="#FFFFFF",
                font_weight="700",
                font_family=TYPOGRAPHY["display"],
                font_size="0.84rem",
                line_height="1.1",
                flex="1",
                min_width="0",
                overflow="hidden",
                text_overflow="ellipsis",
                white_space="nowrap",
            ),
            rx.icon("chevron_up", size=13, color="#7F93A5", flex_shrink="0"),
            align="center",
            spacing="3",
            width="100%",
        ),
        width="100%",
        min_height="46px",
        padding="9px 12px",
        border_radius=RADII["md"],
        background="linear-gradient(180deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.03) 100%)",
        border="1px solid rgba(255,255,255,0.05)",
        box_shadow="inset 0 1px 0 rgba(255,255,255,0.03)",
        _hover={"background": "rgba(255,255,255,0.07)"},
    )

    content = rx.popover.content(
        rx.vstack(
            rx.vstack(
                rx.text(
                    AppState.current_user_name,
                    color=COLORS["text"],
                    font_weight="700",
                    font_family=TYPOGRAPHY["display"],
                    font_size="0.98rem",
                ),
                rx.text(
                    AppState.current_user_email,
                    color=COLORS["text_muted"],
                    font_size="0.82rem",
                    line_height="1.45",
                    overflow_wrap="anywhere",
                    word_break="break-word",
                    width="100%",
                ),
                spacing="1",
                align="start",
                width="100%",
            ),
            rx.button(
                "Encerrar sessão",
                on_click=AppState.logout,
                width="100%",
                background=COLORS["sidebar"],
                color="#FFFFFF",
                border="1px solid rgba(18,48,71,0.12)",
                border_radius=RADII["sm"],
                font_weight="700",
                _hover={"background": COLORS["sidebar_alt"]},
            ),
            spacing="3",
            align="stretch",
            width="100%",
        ),
        width=SIDEBAR_INNER_WIDTH,
        side="top",
        align="center",
        side_offset=10,
        collision_padding=12,
        padding="14px",
        border_radius=RADII["md"],
        background="linear-gradient(180deg, #FFFFFF 0%, #F7FAFC 100%)",
        border=f"1px solid {COLORS['border']}",
        box_shadow="0 16px 32px rgba(6, 16, 24, 0.18)",
    )

    return rx.popover.root(
        rx.popover.trigger(trigger),
        content,
    )


def _collapsed_session_footer() -> rx.Component:
    return rx.button(
        rx.center(
            rx.text(
                AppState.profile_initials,
                color="#EAF4FA",
                font_family=TYPOGRAPHY["display"],
                font_weight="700",
                font_size="0.78rem",
                letter_spacing="0.02em",
            ),
            width="34px",
            height="34px",
            border_radius="999px",
            background="linear-gradient(180deg, rgba(255,255,255,0.10) 0%, rgba(255,255,255,0.06) 100%)",
            border="1px solid rgba(255,255,255,0.06)",
        ),
        on_click=AppState.toggle_sidebar,
        width="100%",
        min_height="46px",
        padding="8px",
        border_radius=RADII["md"],
        background="linear-gradient(180deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.03) 100%)",
        border="1px solid rgba(255,255,255,0.05)",
        box_shadow="inset 0 1px 0 rgba(255,255,255,0.03)",
        _hover={"background": "rgba(255,255,255,0.07)"},
        title=AppState.current_user_name,
    )


def _session_footer() -> rx.Component:
    return rx.cond(
        AppState.sidebar_collapsed,
        _collapsed_session_footer(),
        _expanded_session_footer(),
    )


def _workspace_sidebar() -> rx.Component:
    return rx.el.aside(
        rx.flex(
            rx.vstack(
                _sidebar_brand(),
                _menu_block(),
                spacing=rx.cond(AppState.sidebar_collapsed, "3", "4"),
                align=rx.cond(AppState.sidebar_collapsed, "center", "stretch"),
                width="100%",
            ),
            _session_footer(),
            direction="column",
            justify="between",
            align="stretch",
            width="100%",
            height="100%",
        ),
        _sidebar_toggle_handle(),
        position="fixed",
        left="0",
        top="0",
        width=AppState.sidebar_width,
        height="100vh",
        padding=rx.cond(AppState.sidebar_collapsed, "16px 12px", "20px"),
        background=f"linear-gradient(180deg, {COLORS['sidebar']} 0%, {COLORS['sidebar_alt']} 100%)",
        border_right="1px solid rgba(255,255,255,0.05)",
        box_shadow="inset -1px 0 0 rgba(255,255,255,0.02)",
        overflow="visible",
        z_index="10",
        transition="width 0.22s ease, padding 0.22s ease",
    )


def workspace_shell(content: rx.Component) -> rx.Component:
    return rx.el.div(
        _workspace_sidebar(),
        rx.el.main(
            rx.box(
                content,
                width="100%",
                max_width="1280px",
                margin="0 auto",
            ),
            margin_left=AppState.sidebar_width,
            width=AppState.main_canvas_width,
            height="100vh",
            overflow_y="auto",
            overflow_x="hidden",
            padding_x=SPACE["xl"],
            padding_top=SPACE["xl"],
            padding_bottom=SPACE["xl"],
            background=f"radial-gradient(circle at top right, rgba(0,122,94,0.08) 0%, rgba(255,255,255,0) 26%), radial-gradient(circle at top left, {COLORS['accent_glow']} 0%, rgba(255,255,255,0) 24%), linear-gradient(180deg, {COLORS['surface']} 0%, #F7FAFC 100%)",
            transition="margin-left 0.22s ease, width 0.22s ease",
        ),
        width="100vw",
        height="100vh",
        overflow="hidden",
        background=COLORS["surface"],
    )
