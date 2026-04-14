from __future__ import annotations

import reflex as rx


COLORS = {
    "brand": "#007A5E",
    "brand_alt": "#008064",
    "brand_soft": "#D9F1EA",
    "brand_warm": "#F2B400",
    "brand_warm_soft": "#FFF4CC",
    "bg": "#0E2333",
    "bg_alt": "#123047",
    "sidebar": "#123047",
    "sidebar_alt": "#163A55",
    "surface": "#F4F6F8",
    "surface_alt": "#EAF0F4",
    "panel": "#FFFFFF",
    "panel_alt": "#F7FAFC",
    "chrome": "#D6DEE5",
    "border": "#CDD7E0",
    "border_strong": "#98A8B8",
    "text": "#1A2631",
    "text_muted": "#6B7280",
    "text_soft": "#8092A3",
    "accent": "#1FA3A3",
    "accent_dark": "#167D7D",
    "accent_soft": "#D8F2F2",
    "accent_glow": "rgba(31, 163, 163, 0.14)",
    "electric": "#1D4F73",
    "electric_soft": "#DFEBF4",
    "amber": "#D99A00",
    "amber_soft": "#FFF0C4",
    "success": "#1F8F5F",
    "success_soft": "#D9F2E7",
    "danger": "#C84C4C",
    "danger_soft": "#F9E3E3",
    "info": "#1D4F73",
    "info_soft": "#E2ECF5",
    "graphite": "#2B3440",
}

RADII = {
    "xs": "8px",
    "sm": "12px",
    "md": "18px",
    "lg": "24px",
    "xl": "32px",
    "pill": "999px",
}

SHADOWS = {
    "soft": "0 24px 60px rgba(8, 16, 24, 0.10)",
    "panel": "0 10px 26px rgba(15, 23, 42, 0.05)",
    "glow": "0 0 0 1px rgba(21, 183, 210, 0.05), 0 18px 42px rgba(21, 183, 210, 0.10)",
}

SPACE = {
    "xs": "6px",
    "sm": "12px",
    "md": "16px",
    "lg": "24px",
    "xl": "32px",
    "2xl": "44px",
    "3xl": "56px",
}

TYPOGRAPHY = {
    "display": "\"Space Grotesk\", \"Segoe UI\", sans-serif",
    "body": "\"IBM Plex Sans\", \"Segoe UI\", sans-serif",
    "mono": "\"IBM Plex Mono\", Consolas, monospace",
}

BRANDING = {
    "org_name": "Bem Brasil",
    "app_name": "PainelManuten\u00e7\u00e3o",
    "app_subtitle": "Gest\u00e3o Industrial",
}

COLOR_ROLES = {
    "brand_green": "Assinatura institucional da Bem Brasil, usada em branding, selos de marca e detalhes de autoridade.",
    "brand_yellow": "Apoio institucional pontual para reforcos de marca e pequenos destaques de apoio.",
    "petroleum_blue": "Cor estrutural principal do produto, aplicada em sidebar, fundos tecnicos e navegacao principal.",
    "industrial_blue": "Camada secundaria para headers, informacao contextual e contraste tecnico.",
    "cyan_accent": "Interacoes, foco visual, links e realces operacionais discretos.",
    "neutral_surfaces": "Fundos, superficies, bordas e areas de leitura para manter clareza e densidade produtiva.",
    "status_colors": "Ambar para atencao, verde para sucesso/liberacao e vermelho para erro, bloqueio ou criticidade.",
}

GLOBAL_STYLE = {
    "font_family": TYPOGRAPHY["body"],
    "background_color": COLORS["surface"],
    "color": COLORS["text"],
}


def app_theme() -> rx.Component:
    return rx.theme(
        has_background=True,
        appearance="light",
        accent_color="cyan",
        gray_color="slate",
        radius="large",
    )
