from __future__ import annotations

from django.views.generic import DetailView, TemplateView

from apps.access.mixins import AppPermissionRequiredMixin, SidebarContextMixin
from apps.ordens_servico.forms import ServiceOrderFilterForm
from apps.ordens_servico.models import ExternalServiceOrder
from apps.ordens_servico.services import (
    apply_service_order_filters,
    base_service_order_queryset,
    paginate_service_order_queryset,
    resolve_area_from_code,
    serialize_query_without_page,
)
from common.permissions import PermissionName, ensure_area_access, get_allowed_areas, is_global_user


class ServiceOrderBaseMixin(SidebarContextMixin):
    active_nav_slug = "ordens"

    def get_allowed_areas(self):
        if is_global_user(self.request.user):
            return list(self.request.user.allowed_areas.model.objects.order_by("name"))
        areas = get_allowed_areas(self.request.user)
        return areas or list(self.request.user.allowed_areas.all())

    def get_sidebar_area(self):
        if hasattr(self, "object") and getattr(self, "object", None) is not None:
            return self.object.motor.equipment.area
        return resolve_area_from_code(self.request.user, self.request.GET.get("area"))


class ServiceOrderListView(AppPermissionRequiredMixin, ServiceOrderBaseMixin, TemplateView):
    template_name = "ordens_servico/list.html"
    partial_template_name = "ordens_servico/partials/list_content.html"
    permission_required = PermissionName.VIEW_AREA_DATA

    def get_template_names(self):
        if getattr(self.request, "htmx", False):
            return [self.partial_template_name]
        return [self.template_name]

    def get_filter_form(self):
        return ServiceOrderFilterForm(data=self.request.GET or None, allowed_areas=self.get_allowed_areas())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = base_service_order_queryset(self.request.user)
        filter_form = self.get_filter_form()
        if filter_form.is_valid():
            queryset = apply_service_order_filters(queryset, filter_form.cleaned_data, user=self.request.user)
        page_obj = paginate_service_order_queryset(queryset, self.request.GET.get("page"))
        context.update(
            {
                "page_title": "Ordens de Serviço",
                "page_eyebrow": "Servico externo",
                "filter_form": filter_form,
                "page_obj": page_obj,
                "object_list": page_obj.object_list,
                "filter_query": serialize_query_without_page(self.request.GET),
                "total_count": queryset.count(),
            }
        )
        return context


class ServiceOrderDetailView(AppPermissionRequiredMixin, ServiceOrderBaseMixin, DetailView):
    template_name = "ordens_servico/detail.html"
    context_object_name = "service_order"
    queryset = ExternalServiceOrder.objects.select_related(
        "motor__equipment",
        "motor__equipment__area",
        "authorized_by_user",
        "registered_by_user",
    )
    permission_required = PermissionName.VIEW_AREA_DATA

    def get_object(self, queryset=None):
        service_order = super().get_object(queryset)
        ensure_area_access(self.request.user, service_order.motor.equipment.area)
        return service_order

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"OS {self.object.work_order_number}"
        context["page_eyebrow"] = "Ordem de serviço"
        return context
