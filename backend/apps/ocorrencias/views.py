from __future__ import annotations

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import CreateView, DetailView, TemplateView, UpdateView, View

from apps.access.mixins import AppPermissionRequiredMixin, SidebarContextMixin
from apps.equipamentos.models import Equipment
from apps.ocorrencias.forms import (
    OccurrenceFilterForm,
    OccurrenceForm,
    OccurrenceHistoryFilterForm,
    OccurrenceStatusForm,
)
from apps.ocorrencias.models import Occurrence
from apps.ocorrencias.services import (
    apply_history_filters,
    apply_occurrence_filters,
    base_occurrence_queryset,
    build_occurrence_history_queryset,
    build_occurrence_timeline,
    create_occurrence_from_form,
    paginate_history_queryset,
    paginate_occurrence_queryset,
    resolve_area_from_code,
    serialize_query_without_page,
    update_occurrence_from_form,
    update_occurrence_status,
)
from common.permissions import (
    PermissionName,
    ensure_area_access,
    get_allowed_areas,
    has_permission,
    is_global_user,
)


class OccurrenceBaseMixin(SidebarContextMixin):
    active_nav_slug = "ocorrencias"

    def get_allowed_areas(self):
        if is_global_user(self.request.user):
            return list(self.request.user.allowed_areas.model.objects.order_by("name"))
        areas = get_allowed_areas(self.request.user)
        return areas or list(self.request.user.allowed_areas.all())

    def get_sidebar_area(self):
        if hasattr(self, "object") and getattr(self, "object", None) is not None:
            return self.object.area
        return resolve_area_from_code(self.request.user, self.request.GET.get("area"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["can_create_occurrence"] = has_permission(self.request.user, PermissionName.CREATE_OCCURRENCES)
        context["can_edit_occurrence"] = has_permission(self.request.user, PermissionName.EDIT_OCCURRENCES)
        return context


class OccurrenceListView(AppPermissionRequiredMixin, OccurrenceBaseMixin, TemplateView):
    template_name = "ocorrencias/list.html"
    partial_template_name = "ocorrencias/partials/list_content.html"
    permission_required = PermissionName.VIEW_AREA_DATA
    active_nav_slug = "ocorrencias"

    def get_filter_form(self):
        return OccurrenceFilterForm(
            data=self.request.GET or None,
            user=self.request.user,
            allowed_areas=self.get_allowed_areas(),
        )

    def get_template_names(self):
        if getattr(self.request, "htmx", False):
            return [self.partial_template_name]
        return [self.template_name]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = base_occurrence_queryset(self.request.user)
        filter_form = self.get_filter_form()
        if filter_form.is_valid():
            queryset = apply_occurrence_filters(queryset, filter_form.cleaned_data)
        page_obj = paginate_occurrence_queryset(queryset, self.request.GET.get("page"))
        context.update(
            {
                "page_title": "Ocorrencias",
                "page_eyebrow": "Fluxo operacional",
                "filter_form": filter_form,
                "page_obj": page_obj,
                "object_list": page_obj.object_list,
                "filter_query": serialize_query_without_page(self.request.GET),
                "total_count": queryset.count(),
            }
        )
        return context


class OccurrenceDetailView(AppPermissionRequiredMixin, OccurrenceBaseMixin, DetailView):
    template_name = "ocorrencias/detail.html"
    queryset = Occurrence.objects.select_related(
        "equipment",
        "equipment__unidade",
        "equipment__unidade__fabrica",
        "area",
        "location",
        "location__unidade",
        "location__unidade__fabrica",
        "unidade",
        "unidade__fabrica",
        "responsible_collaborator",
        "reported_by_user",
    )
    permission_required = PermissionName.VIEW_AREA_DATA
    context_object_name = "occurrence"

    def get_object(self, queryset=None):
        occurrence = super().get_object(queryset)
        ensure_area_access(self.request.user, occurrence.area)
        return occurrence

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Ocorrencia {self.object.equipment.code}"
        context["page_eyebrow"] = "Detalhe operacional"
        context["timeline_events"] = build_occurrence_timeline(self.object)[:15]
        context["status_form"] = OccurrenceStatusForm(initial={"status": self.object.status})
        context["related_occurrences"] = (
            self.object.equipment.occurrences.select_related("reported_by_user")
            .exclude(pk=self.object.pk)
            .order_by("-occurred_at", "-created_at")[:6]
        )
        return context


class OccurrenceCreateView(AppPermissionRequiredMixin, OccurrenceBaseMixin, CreateView):
    template_name = "ocorrencias/form.html"
    form_class = OccurrenceForm
    permission_required = PermissionName.CREATE_OCCURRENCES

    def get_initial_equipment(self):
        equipment_id = self.request.GET.get("equipment")
        if not equipment_id:
            return None
        equipment = Equipment.objects.select_related("area", "location").filter(pk=equipment_id).first()
        if equipment is None:
            return None
        ensure_area_access(self.request.user, equipment.area)
        return equipment

    def get_sidebar_area(self):
        equipment = self.get_initial_equipment()
        if equipment is not None:
            return equipment.area
        return super().get_sidebar_area()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        kwargs["allowed_areas"] = get_allowed_areas(self.request.user)
        kwargs["initial_equipment"] = self.get_initial_equipment()
        return kwargs

    def form_valid(self, form):
        self.object = create_occurrence_from_form(form, self.request.user)
        messages.success(self.request, "Ocorrencia registrada com sucesso.")
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse("ocorrencias:detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Nova ocorrencia"
        context["page_eyebrow"] = "Registro operacional"
        return context


class OccurrenceUpdateView(AppPermissionRequiredMixin, OccurrenceBaseMixin, UpdateView):
    template_name = "ocorrencias/form.html"
    form_class = OccurrenceForm
    model = Occurrence
    permission_required = PermissionName.EDIT_OCCURRENCES

    def get_object(self, queryset=None):
        occurrence = super().get_object(queryset)
        ensure_area_access(self.request.user, occurrence.area)
        return occurrence

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        kwargs["allowed_areas"] = get_allowed_areas(self.request.user)
        return kwargs

    def form_valid(self, form):
        self.object = update_occurrence_from_form(form, self.request.user)
        messages.success(self.request, "Ocorrencia atualizada com sucesso.")
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse("ocorrencias:detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Editar ocorrencia {self.object.equipment.code}"
        context["page_eyebrow"] = "Atualizacao"
        return context


class OccurrenceStatusUpdateView(AppPermissionRequiredMixin, View):
    permission_required = PermissionName.EDIT_OCCURRENCES

    def post(self, request, *args, **kwargs):
        occurrence = get_object_or_404(
            Occurrence.objects.select_related("area", "equipment"),
            pk=kwargs["pk"],
        )
        ensure_area_access(request.user, occurrence.area)
        form = OccurrenceStatusForm(request.POST)
        if not form.is_valid():
            messages.error(request, "Nao foi possivel atualizar o status da ocorrencia.")
            return redirect(reverse("ocorrencias:detail", kwargs={"pk": occurrence.pk}))

        update_occurrence_status(
            occurrence,
            status=form.cleaned_data["status"],
            actor=request.user,
            note=form.cleaned_data.get("note", ""),
        )
        messages.success(request, "Status da ocorrencia atualizado.")
        return redirect(reverse("ocorrencias:detail", kwargs={"pk": occurrence.pk}))


class OccurrenceHistoryView(AppPermissionRequiredMixin, OccurrenceBaseMixin, TemplateView):
    template_name = "ocorrencias/history.html"
    partial_template_name = "ocorrencias/partials/history_content.html"
    permission_required = PermissionName.VIEW_AREA_DATA
    active_nav_slug = "historico"

    def get_filter_form(self):
        return OccurrenceHistoryFilterForm(data=self.request.GET or None, allowed_areas=self.get_allowed_areas())

    def get_template_names(self):
        if getattr(self.request, "htmx", False):
            return [self.partial_template_name]
        return [self.template_name]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = build_occurrence_history_queryset(self.request.user)
        filter_form = self.get_filter_form()
        if filter_form.is_valid():
            queryset = apply_history_filters(queryset, filter_form.cleaned_data)
        page_obj = paginate_history_queryset(queryset, self.request.GET.get("page"))
        context.update(
            {
                "page_title": "Historico",
                "page_eyebrow": "Timeline operacional",
                "filter_form": filter_form,
                "page_obj": page_obj,
                "object_list": page_obj.object_list,
                "filter_query": serialize_query_without_page(self.request.GET),
                "total_count": queryset.count(),
            }
        )
        return context
