from __future__ import annotations

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import CreateView, DetailView, TemplateView, UpdateView, View

from apps.access.mixins import AppPermissionRequiredMixin, SidebarContextMixin
from apps.equipamentos.forms import EquipmentFilterForm, EquipmentForm
from apps.equipamentos.models import Equipment
from apps.equipamentos.services import (
    apply_equipment_filters,
    base_equipment_queryset,
    create_equipment_from_form,
    paginate_equipment_queryset,
    resolve_area_from_code,
    serialize_query_without_page,
    toggle_equipment_active_state,
    update_equipment_from_form,
)
from apps.ocorrencias.services import recent_occurrences_for_equipment
from common.enums import EquipmentStatus, EquipmentType, OccurrenceStatus
from common.permissions import PermissionName, can_manage_area_data, ensure_area_access, get_allowed_areas, has_permission, is_global_user


class EquipmentBaseMixin(SidebarContextMixin):
    active_nav_slug = "equipamentos"

    def get_active_nav_slug(self):
        equipment_type = self.request.GET.get("equipment_type")
        if equipment_type == EquipmentType.MOTOR:
            return "motores"
        if hasattr(self, "object") and getattr(self, "object", None) is not None:
            if self.object.type == EquipmentType.MOTOR:
                return "motores"
        return self.active_nav_slug

    def get_sidebar_area(self):
        if hasattr(self, "object") and getattr(self, "object", None) is not None:
            return self.object.area
        return resolve_area_from_code(self.request.user, self.request.GET.get("area"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["can_manage_equipment"] = can_manage_area_data(self.request.user)
        context["can_create_occurrence"] = has_permission(self.request.user, PermissionName.CREATE_OCCURRENCES)
        return context


class EquipmentListView(AppPermissionRequiredMixin, EquipmentBaseMixin, TemplateView):
    template_name = "equipamentos/list.html"
    partial_template_name = "equipamentos/partials/list_content.html"
    permission_required = PermissionName.VIEW_AREA_DATA

    def get_allowed_areas(self):
        if is_global_user(self.request.user):
            return list(self.request.user.allowed_areas.model.objects.order_by("name"))
        areas = get_allowed_areas(self.request.user)
        return areas or list(self.request.user.allowed_areas.all())

    def get_filter_form(self):
        return EquipmentFilterForm(
            data=self.request.GET or None,
            user=self.request.user,
            allowed_areas=self.get_allowed_areas(),
        )

    def get_template_names(self):
        if getattr(self.request, "htmx", False):
            return [self.partial_template_name]
        return [self.template_name]

    def build_summary(self, queryset):
        return {
            "total": queryset.count(),
            "active": queryset.filter(status=EquipmentStatus.ACTIVE).count(),
            "motors": queryset.filter(type=EquipmentType.MOTOR).count(),
            "instruments": queryset.filter(type=EquipmentType.INSTRUMENT).count(),
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = base_equipment_queryset(self.request.user)
        filter_form = self.get_filter_form()
        if filter_form.is_valid():
            queryset = apply_equipment_filters(queryset, filter_form.cleaned_data)
        page_obj = paginate_equipment_queryset(queryset, self.request.GET.get("page"))
        context.update(
            {
                "page_title": "Equipamentos",
                "equipment_summary": self.build_summary(queryset),
                "filter_form": filter_form,
                "page_obj": page_obj,
                "object_list": page_obj.object_list,
                "filter_query": serialize_query_without_page(self.request.GET),
                "total_count": queryset.count(),
            }
        )
        return context


class EquipmentDetailView(AppPermissionRequiredMixin, EquipmentBaseMixin, DetailView):
    template_name = "equipamentos/detail.html"
    queryset = Equipment.objects.select_related(
        "area",
        "unidade",
        "unidade__fabrica",
        "location",
        "location__unidade",
        "location__unidade__fabrica",
        "motor",
        "instrument",
    )
    permission_required = PermissionName.VIEW_AREA_DATA
    context_object_name = "equipment"

    def get_object(self, queryset=None):
        equipment = super().get_object(queryset)
        ensure_area_access(self.request.user, equipment.area)
        return equipment

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = self.object.code
        context["operational_summary"] = {
            "total_occurrences": self.object.occurrences.count(),
            "open_occurrences": self.object.occurrences.filter(
                status__in=[
                    OccurrenceStatus.OPEN,
                    OccurrenceStatus.IN_PROGRESS,
                    OccurrenceStatus.WAITING_PARTS,
                ]
            ).count(),
            "movements": self.object.movements.count(),
            "registered_at": self.object.registered_at,
        }
        context["movements"] = self.object.movements.select_related("moved_by_user", "new_location")[:10]
        context["recent_occurrences"] = recent_occurrences_for_equipment(self.object, limit=6)
        return context


class EquipmentCreateView(AppPermissionRequiredMixin, EquipmentBaseMixin, CreateView):
    template_name = "equipamentos/form.html"
    form_class = EquipmentForm
    permission_required = PermissionName.MANAGE_AREA_DATA

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        kwargs["allowed_areas"] = get_allowed_areas(self.request.user)
        return kwargs

    def form_valid(self, form):
        self.object = create_equipment_from_form(form)
        messages.success(self.request, "Equipamento criado com sucesso.")
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse("equipamentos:detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Novo equipamento"
        return context


# TODO: adicionar view de edição de Motor com MotorForm
class EquipmentUpdateView(AppPermissionRequiredMixin, EquipmentBaseMixin, UpdateView):
    template_name = "equipamentos/form.html"
    form_class = EquipmentForm
    model = Equipment
    permission_required = PermissionName.MANAGE_AREA_DATA

    def get_object(self, queryset=None):
        equipment = super().get_object(queryset)
        ensure_area_access(self.request.user, equipment.area)
        return equipment

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        kwargs["allowed_areas"] = get_allowed_areas(self.request.user)
        return kwargs

    def form_valid(self, form):
        self.object = update_equipment_from_form(form)
        messages.success(self.request, "Equipamento atualizado com sucesso.")
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse("equipamentos:detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Editar {self.object.code}"
        return context


class EquipmentToggleStatusView(AppPermissionRequiredMixin, View):
    permission_required = PermissionName.MANAGE_AREA_DATA

    def post(self, request, *args, **kwargs):
        equipment = get_object_or_404(Equipment, pk=kwargs["pk"])
        ensure_area_access(request.user, equipment.area)
        toggle_equipment_active_state(equipment)
        messages.success(request, "Status do equipamento atualizado.")
        return redirect(reverse("equipamentos:detail", kwargs={"pk": equipment.pk}))
