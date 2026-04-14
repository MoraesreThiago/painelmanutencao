from __future__ import annotations

import os

# This project is currently more stable on Windows/OneDrive with npm than bun.
os.environ.setdefault("REFLEX_USE_NPM", "1")

import reflex as rx

from utils.reflex_compat_plugin import ReflexCompatibilityPlugin


config = rx.Config(
    app_name="runtime",
    frontend_port=3000,
    backend_port=3001,
    plugins=[
        ReflexCompatibilityPlugin(),
        rx.plugins.SitemapPlugin(),
    ],
)
