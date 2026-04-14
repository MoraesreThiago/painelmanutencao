from __future__ import annotations

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied

from apps.access.forms import ContextSwitchForm
from apps.access.services import (
    build_current_context_summary,
    build_sidebar_sections,
)
from common.permissions import get_user_role_name
from common.permissions import PermissionName, ensure_area_access, has_actual_permission, has_permission


class AppPermissionRequiredMixin(LoginRequiredMixin):
    permission_required = None

    def dispatch(self, request, *args, **kwargs):
        if self.permission_required and not has_permission(request.user, self.permission_required):
            raise PermissionDenied("Usuário sem permissão para acessar esta página.")
        return super().dispatch(request, *args, **kwargs)


class AreaContextMixin:
    area = None

    def resolve_area(self):
        return None

    def get_area(self):
        if self.area is None:
            self.area = self.resolve_area()
            ensure_area_access(self.request.user, self.area)
        return self.area


class SidebarContextMixin:
    active_nav_slug = "painel"

    def get_active_nav_slug(self):
        return self.active_nav_slug

    def get_sidebar_area(self):
        return getattr(self, "area", None)

    def get_sidebar_sections(self):
        return build_sidebar_sections(
            self.request.user,
            active_slug=self.get_active_nav_slug(),
            area=self.get_sidebar_area(),
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_area = self.get_sidebar_area()
        context["sidebar_sections"] = self.get_sidebar_sections()
        context["active_nav_slug"] = self.get_active_nav_slug()
        context["current_area"] = current_area
        context["can_assume_context"] = has_actual_permission(self.request.user, PermissionName.ASSUME_AREA_CONTEXT)
        context["current_context_summary"] = build_current_context_summary(self.request.user, area=current_area)
        if context["can_assume_context"]:
            context["context_switch_form"] = ContextSwitchForm(
                user=self.request.user,
                initial={
                    "area": getattr(current_area, "code", ""),
                    "role_name": getattr(get_user_role_name(self.request.user), "value", ""),
                },
            )
        return context
