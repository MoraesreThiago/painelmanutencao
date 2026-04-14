from __future__ import annotations

from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import TemplateView

from apps.access.forms import ContextSwitchForm
from apps.access.mixins import AreaContextMixin, SidebarContextMixin
from apps.access.services import (
    build_dashboard_payload,
    build_monthly_summary_payload,
    build_power_monitoring_payload,
    build_panel_href,
    is_electrical_context,
)
from apps.unidades.models import Area
from common.middleware import ASSUMED_ROLE_SESSION_KEY
from common.enums import AreaCode
from common.permissions import PermissionName, can_view_area_data, can_view_reports, ensure_area_access, has_actual_permission


class LegacyDashboardRedirectView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        area_code = request.GET.get("area")
        area = getattr(request.user, "area", None)
        if area_code:
            area = get_object_or_404(Area, code=area_code)
            ensure_area_access(request.user, area)
        return redirect(build_panel_href(area))


class ContextSwitchView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        if not has_actual_permission(request.user, PermissionName.ASSUME_AREA_CONTEXT):
            raise PermissionDenied("Usuario sem permissao para alterar contexto.")

        form = ContextSwitchForm(request.POST, user=request.user)
        if not form.is_valid():
            messages.error(request, "Nao foi possivel aplicar o contexto selecionado.")
            return redirect(build_panel_href(getattr(request.user, "area", None)))

        area = get_object_or_404(Area, code=form.cleaned_data["area"])
        ensure_area_access(request.user, area)
        request.session[ASSUMED_ROLE_SESSION_KEY] = form.cleaned_data["role_name"]
        messages.success(request, "Contexto aplicado com sucesso.", extra_tags="flash-short")
        return redirect(build_panel_href(area))


class ContextResetView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        if not has_actual_permission(request.user, PermissionName.ASSUME_AREA_CONTEXT):
            raise PermissionDenied("Usuario sem permissao para restaurar contexto.")

        request.session.pop(ASSUMED_ROLE_SESSION_KEY, None)
        area_code = request.POST.get("area")
        area = getattr(request.user, "area", None)
        if area_code:
            area = get_object_or_404(Area, code=area_code)
            ensure_area_access(request.user, area)
        messages.success(request, "Contexto de administrador restaurado.")
        return redirect(build_panel_href(area))


class DashboardView(LoginRequiredMixin, SidebarContextMixin, TemplateView):
    template_name = "access/dashboard.html"
    active_nav_slug = "painel"

    def get_dashboard_area(self):
        area_code = self.request.GET.get("area")
        if not area_code:
            return getattr(self.request.user, "area", None)
        area = get_object_or_404(Area, code=area_code)
        ensure_area_access(self.request.user, area)
        return area

    def get_sidebar_area(self):
        return self.get_dashboard_area()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        dashboard_area = self.get_dashboard_area()
        context.update(build_dashboard_payload(self.request.user, area=dashboard_area))
        context["page_title"] = dashboard_area.name if dashboard_area else "Dashboard"
        context["page_eyebrow"] = "Visao global"
        context["dashboard_area"] = dashboard_area
        return context


class DashboardMetricsPartialView(LoginRequiredMixin, TemplateView):
    template_name = "access/partials/dashboard_metrics.html"

    def get_context_data(self, **kwargs):
        return build_dashboard_payload(self.request.user)


class MonthlySummaryView(LoginRequiredMixin, SidebarContextMixin, TemplateView):
    template_name = "access/monthly_summary.html"
    active_nav_slug = "relatorios"

    def get_summary_area(self):
        area_code = self.request.GET.get("area")
        if not area_code:
            return getattr(self.request.user, "area", None)
        area = get_object_or_404(Area, code=area_code)
        ensure_area_access(self.request.user, area)
        return area

    def get_sidebar_area(self):
        return self.get_summary_area()

    def dispatch(self, request, *args, **kwargs):
        if not can_view_reports(request.user):
            raise PermissionDenied("Usuario sem permissao para acessar relatorios.")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        summary_area = self.get_summary_area()
        context.update(build_monthly_summary_payload(self.request.user, area=summary_area))
        context["page_title"] = "Resumo Mensal"
        context["page_eyebrow"] = summary_area.name if summary_area else "Relatorios"
        context["summary_area"] = summary_area
        return context


class PowerMonitoringView(LoginRequiredMixin, SidebarContextMixin, TemplateView):
    template_name = "access/power_monitoring.html"
    active_nav_slug = "energia"

    def get_monitoring_area(self):
        area_code = self.request.GET.get("area")
        if not area_code:
            return getattr(self.request.user, "area", None)
        area = get_object_or_404(Area, code=area_code)
        ensure_area_access(self.request.user, area)
        return area

    def get_sidebar_area(self):
        return self.get_monitoring_area()

    def dispatch(self, request, *args, **kwargs):
        if not can_view_area_data(request.user):
            raise PermissionDenied("Usuário sem permissão para acessar monitoramento de energia.")
        if not is_electrical_context(request.user, area=self.get_monitoring_area()):
            raise PermissionDenied("Monitoramento de energia disponível apenas para a área Elétrica.")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        monitoring_area = self.get_monitoring_area()
        context.update(build_power_monitoring_payload(area=monitoring_area))
        context["page_title"] = "Tensão, Geração e Consumo"
        context["page_eyebrow"] = monitoring_area.name if monitoring_area else "Energia"
        context["monitoring_area"] = monitoring_area
        return context


class BaseWorkspaceView(LoginRequiredMixin, AreaContextMixin, SidebarContextMixin, TemplateView):
    template_name = "access/workspace.html"
    area_code: str = ""
    active_nav_slug = "painel"

    def resolve_area(self):
        return get_object_or_404(Area, code=self.area_code)

    def get_context_data(self, **kwargs):
        area = self.get_area()
        context = super().get_context_data(**kwargs)
        context.update(build_dashboard_payload(self.request.user, area=area))
        context["area"] = area
        context["page_title"] = area.name
        context["page_eyebrow"] = area.get_code_display()
        return context


class ElectricalWorkspaceView(BaseWorkspaceView):
    template_name = "access/workspace_eletrica.html"
    area_code = AreaCode.ELETRICA


class MechanicalWorkspaceView(BaseWorkspaceView):
    template_name = "access/workspace_mecanica.html"
    area_code = AreaCode.MECANICA


class InstrumentationWorkspaceView(BaseWorkspaceView):
    template_name = "access/workspace_instrumentacao.html"
    area_code = AreaCode.INSTRUMENTACAO
