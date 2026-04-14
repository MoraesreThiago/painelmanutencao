from __future__ import annotations

from django.views.generic import TemplateView

from apps.access.mixins import AppPermissionRequiredMixin, SidebarContextMixin
from apps.colaboradores.forms import TeamFilterForm
from apps.colaboradores.services import (
    apply_team_physical_scope,
    apply_team_filters,
    base_team_queryset,
    build_team_summary,
    paginate_team_queryset,
    resolve_team_area,
    serialize_query_without_page,
)
from django.core.exceptions import PermissionDenied

from common.permissions import PermissionName, can_manage_team


class TeamManagementAreaMixin(SidebarContextMixin):
    active_nav_slug = "equipe"
    area = None

    def get_area(self):
        if self.area is None:
            self.area = resolve_team_area(self.request.user, self.request.GET.get("area"))
        return self.area

    def get_sidebar_area(self):
        return self.get_area()


class TeamManagementListView(AppPermissionRequiredMixin, TeamManagementAreaMixin, TemplateView):
    template_name = "colaboradores/list.html"
    partial_template_name = "colaboradores/partials/list_content.html"
    permission_required = PermissionName.MANAGE_AREA_DATA

    def dispatch(self, request, *args, **kwargs):
        if not can_manage_team(request.user):
            raise PermissionDenied("Usuario sem permissao para acessar a gestao da equipe.")
        return super().dispatch(request, *args, **kwargs)

    def get_template_names(self):
        if getattr(self.request, "htmx", False):
            return [self.partial_template_name]
        return [self.template_name]

    def get_filter_form(self):
        return TeamFilterForm(data=self.request.GET or None, user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = base_team_queryset(self.request.user, area=self.get_area())
        queryset = apply_team_physical_scope(queryset, self.request.user)
        filter_form = self.get_filter_form()
        if filter_form.is_valid():
            queryset = apply_team_filters(queryset, filter_form.cleaned_data)
        page_obj = paginate_team_queryset(queryset, self.request.GET.get("page"))
        current_area = self.get_area()
        context.update(
            {
                "page_title": "Gestao da equipe",
                "filter_form": filter_form,
                "page_obj": page_obj,
                "object_list": page_obj.object_list,
                "total_count": queryset.count(),
                "filter_query": serialize_query_without_page(self.request.GET),
                "team_summary": build_team_summary(queryset),
                "current_team_area": current_area,
            }
        )
        return context
