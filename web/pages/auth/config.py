from __future__ import annotations

from dataclasses import dataclass

from theme.theme import BRANDING, COLORS, RADII


INPUT_STYLE = {
    "size": "3",
    "width": "100%",
    "background": COLORS["panel_alt"],
    "border": f"1px solid {COLORS['border']}",
    "border_radius": RADII["sm"],
    "min_height": "54px",
    "padding": "0.9rem 1rem",
    "font_size": "1.08rem",
    "font_weight": "500",
    "color": COLORS["text"],
    "box_shadow": "none",
}


@dataclass(frozen=True)
class LoginView:
    title: str
    primary_glow: str
    secondary_glow: str
    logo_opacity: str = "0.14"
    logo_filter: str = "brightness(1.14) saturate(1.06) drop-shadow(0 24px 60px rgba(0,0,0,0.12))"


DEFAULT_LOGIN_VIEW = LoginView(
    title=BRANDING["app_name"],
    primary_glow="radial-gradient(circle, rgba(0,122,94,0.28) 0%, rgba(0,122,94,0.02) 56%, rgba(0,122,94,0) 72%)",
    secondary_glow=f"radial-gradient(circle, {COLORS['accent_glow']} 0%, rgba(31,163,163,0.02) 52%, rgba(31,163,163,0) 72%)",
)

ELECTRICAL_LOGIN_VIEW = LoginView(
    title=BRANDING["app_name"],
    primary_glow="radial-gradient(circle, rgba(29,79,115,0.32) 0%, rgba(29,79,115,0.04) 54%, rgba(29,79,115,0) 72%)",
    secondary_glow="radial-gradient(circle, rgba(31,163,163,0.18) 0%, rgba(31,163,163,0.03) 50%, rgba(31,163,163,0) 72%)",
    logo_opacity="0.16",
    logo_filter="brightness(1.18) saturate(1.08) drop-shadow(0 24px 60px rgba(0,0,0,0.14))",
)

