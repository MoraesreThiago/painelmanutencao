from __future__ import annotations

import reflex as rx


ROUTES_CONFIG_PATH = "app/routes.ts"
COLOR_MODE_PROVIDER_PATH = "components/reflex/radix_themes_color_mode_provider.jsx"


def compile_routes_config() -> tuple[str, str]:
    """Create the React Router config required by the generated Reflex app."""

    return (
        ROUTES_CONFIG_PATH,
        """import { route } from "@react-router/dev/routes";
import { flatRoutes } from "@react-router/fs-routes";

export default [
  ...(await flatRoutes({
    ignoredRouteFiles: ["routes/\\\\[404\\\\]._index.jsx"],
  })),
  route("*", "routes/[404]._index.jsx"),
];
""",
    )


def compile_color_mode_provider() -> tuple[str, str]:
    """Create the Radix color mode bridge expected by Reflex root.jsx."""

    return (
        COLOR_MODE_PROVIDER_PATH,
        """import { createElement } from "react";
import { ColorModeContext } from "$/utils/context";
import { useTheme } from "$/utils/react-theme";

export default function RadixThemesColorModeProvider({ children }) {
  const { theme, resolvedTheme, setTheme } = useTheme();

  return createElement(
    ColorModeContext.Provider,
    {
      value: {
        colorMode: theme,
        resolvedColorMode: resolvedTheme,
        setColorMode: setTheme,
      },
    },
    children,
  );
}
""",
    )


class ReflexCompatibilityPlugin(rx.plugins.Plugin):
    """Project-level fixes for missing generated Reflex frontend files."""

    def pre_compile(self, **context) -> None:
        context["add_save_task"](compile_routes_config)
        context["add_save_task"](compile_color_mode_provider)
