from __future__ import annotations

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View
from django.views.generic import CreateView, DetailView, TemplateView, UpdateView

from apps.access.mixins import AppPermissionRequiredMixin, SidebarContextMixin
from apps.motores.forms import (
    BurnedMotorCaseFilterForm,
    BurnedMotorCaseForm,
    BurnedMotorCaseStatusForm,
    BurnedMotorProcessForm,
    ElectricMotorFilterForm,
    ElectricMotorForm,
)
from apps.motores.models import BurnedMotorCase, BurnedMotorProcess, ElectricMotor
from apps.motores.services import (
    PCMNotificationError,
    apply_burned_case_filters,
    apply_motor_filters,
    base_burned_case_queryset,
    base_motor_queryset,
    build_burned_case_summary,
    build_case_timeline,
    build_motor_catalog_map,
    build_motor_flow_summary,
    build_motor_history,
    motor_snapshot_from_catalog,
    can_manage_burned_motor_flow,
    can_manage_motor_registry,
    create_burned_case_from_form,
    create_burned_process_from_form,
    create_motor_from_form,
    paginate_burned_case_queryset,
    paginate_motor_queryset,
    related_burned_cases_queryset,
    resolve_motor_area,
    send_burned_case_pcm_email,
    serialize_query_without_page,
    update_burned_case_from_form,
    update_burned_case_status,
    update_burned_process_from_form,
    update_motor_from_form,
)
from common.enums import AreaCode
from common.permissions import PermissionName, ensure_area_access


class MotorAreaMixin(SidebarContextMixin):
    active_nav_slug = "motores"
    area = None

    def dispatch(self, request, *args, **kwargs):
        area = (
            getattr(getattr(self, "motor", None), "area", None)
            or getattr(getattr(self, "object", None), "area", None)
            or self.get_area()
        )
        if area.code != AreaCode.ELETRICA:
            raise PermissionDenied("Modulo de motores eletricos disponivel apenas para a area Eletrica.")
        return super().dispatch(request, *args, **kwargs)

    def get_area(self):
        if self.area is None:
            self.area = resolve_motor_area(self.request.user, self.request.GET.get("area"))
        return self.area

    def get_sidebar_area(self):
        if getattr(self, "object", None) is not None:
            return self.object.area
        if getattr(self, "motor", None) is not None:
            return self.motor.area
        return self.get_area()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["can_manage_motor_registry"] = can_manage_motor_registry(self.request.user)
        context["can_manage_burned_motor_flow"] = can_manage_burned_motor_flow(self.request.user)
        context["current_motor_area"] = self.get_sidebar_area()
        return context


class BurnedMotorCaseAreaMixin(MotorAreaMixin):
    active_nav_slug = "motores-queimados"


class MotorObjectMixin(MotorAreaMixin):
    queryset = ElectricMotor.objects.select_related(
        "area",
        "unidade",
        "unidade__fabrica",
        "registered_by_user",
    )

    def get_object(self, queryset=None):
        motor = super().get_object(queryset or self.queryset)
        ensure_area_access(self.request.user, motor.area)
        self.object = motor
        return motor


class BurnedMotorCaseObjectMixin(BurnedMotorCaseAreaMixin):
    queryset = BurnedMotorCase.objects.select_related(
        "motor",
        "motor__unidade",
        "motor__unidade__fabrica",
        "opened_by_user",
        "updated_by_user",
        "area",
        "unidade",
        "unidade__fabrica",
    )
    context_object_name = "case"

    def get_case(self):
        case = get_object_or_404(self.queryset, pk=self.kwargs["pk"])
        ensure_area_access(self.request.user, case.area)
        self.object = case
        return case

    def get_object(self, queryset=None):
        return self.get_case()


class MotorListView(AppPermissionRequiredMixin, MotorAreaMixin, TemplateView):
    template_name = "motores/list.html"
    partial_template_name = "motores/partials/list_content.html"
    permission_required = PermissionName.VIEW_AREA_DATA

    def get_template_names(self):
        if getattr(self.request, "htmx", False):
            return [self.partial_template_name]
        return [self.template_name]

    def get_filter_form(self):
        return ElectricMotorFilterForm(data=self.request.GET or None, user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = base_motor_queryset(self.request.user, area=self.get_area())
        filter_form = self.get_filter_form()
        if filter_form.is_valid():
            queryset = apply_motor_filters(queryset, filter_form.cleaned_data)
        page_obj = paginate_motor_queryset(queryset, self.request.GET.get("page"))
        context.update(
            {
                "page_title": "Motores Eletricos",
                "filter_form": filter_form,
                "page_obj": page_obj,
                "object_list": page_obj.object_list,
                "total_count": queryset.count(),
                "filter_query": serialize_query_without_page(self.request.GET),
            }
        )
        return context


class MotorDetailView(AppPermissionRequiredMixin, MotorObjectMixin, DetailView):
    template_name = "motores/detail.html"
    context_object_name = "motor"
    permission_required = PermissionName.VIEW_AREA_DATA

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = self.object.mo
        context["flow_summary"] = build_motor_flow_summary(self.object)
        context["motor_history"] = build_motor_history(self.object)
        context["related_cases"] = related_burned_cases_queryset(self.object)[:6]
        return context


class MotorCreateView(AppPermissionRequiredMixin, MotorAreaMixin, CreateView):
    template_name = "motores/form.html"
    form_class = ElectricMotorForm
    permission_required = PermissionName.MANAGE_AREA_DATA

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        self.object = create_motor_from_form(form, area=self.get_area(), user=self.request.user)
        messages.success(self.request, "Motor eletrico cadastrado com sucesso.")
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse("motores:detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Novo motor eletrico"
        context["submit_label"] = "Cadastrar motor"
        return context


class MotorUpdateView(AppPermissionRequiredMixin, MotorObjectMixin, UpdateView):
    template_name = "motores/form.html"
    form_class = ElectricMotorForm
    model = ElectricMotor
    permission_required = PermissionName.MANAGE_AREA_DATA

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        self.object = update_motor_from_form(form)
        messages.success(self.request, "Motor eletrico atualizado com sucesso.")
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse("motores:detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Editar {self.object.mo}"
        context["submit_label"] = "Salvar motor"
        return context


class BurnedMotorCaseListView(AppPermissionRequiredMixin, BurnedMotorCaseAreaMixin, TemplateView):
    template_name = "motores/burned_cases/list.html"
    partial_template_name = "motores/burned_cases/partials/list_content.html"
    permission_required = PermissionName.MANAGE_AREA_DATA

    def get_template_names(self):
        if getattr(self.request, "htmx", False):
            return [self.partial_template_name]
        return [self.template_name]

    def get_filter_form(self):
        return BurnedMotorCaseFilterForm(data=self.request.GET or None, user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = base_burned_case_queryset(self.request.user, area=self.get_area())
        filter_form = self.get_filter_form()
        if filter_form.is_valid():
            queryset = apply_burned_case_filters(queryset, filter_form.cleaned_data)
        page_obj = paginate_burned_case_queryset(queryset, self.request.GET.get("page"))
        context.update(
            {
                "page_title": "Motores Queimados",
                "filter_form": filter_form,
                "page_obj": page_obj,
                "object_list": page_obj.object_list,
                "total_count": queryset.count(),
                "filter_query": serialize_query_without_page(self.request.GET),
                "case_summary": build_burned_case_summary(queryset),
            }
        )
        return context


class BurnedMotorCaseFormMixin(BurnedMotorCaseAreaMixin):
    template_name = "motores/burned_cases/form.html"
    form_class = BurnedMotorCaseForm
    permission_required = PermissionName.MANAGE_AREA_DATA

    def get_prefilled_motor(self):
        motor_id = self.request.GET.get("motor")
        if not motor_id:
            return None
        motor = ElectricMotor.objects.select_related("area", "unidade", "unidade__fabrica").filter(pk=motor_id).first()
        if motor is None:
            return None
        ensure_area_access(self.request.user, motor.area)
        return motor

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        kwargs["area"] = self.get_area()
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        prefilled_motor = self.get_prefilled_motor()
        if prefilled_motor is not None:
            initial["motor_lookup"] = prefilled_motor
            initial.update(motor_snapshot_from_catalog(prefilled_motor))
        return initial

    def _send_pcm_if_requested(self):
        return "_send_pcm" in self.request.POST

    def _handle_pcm_email(self, case):
        if not self._send_pcm_if_requested():
            return
        if not case.needs_pcm:
            messages.warning(self.request, "O processo foi salvo sem envio ao PCM porque esse fluxo foi marcado como dispensado.")
            return
        try:
            send_burned_case_pcm_email(case, actor=self.request.user)
            messages.success(self.request, "E-mail do PCM enviado com sucesso.")
        except PCMNotificationError as exc:
            messages.warning(self.request, f"Processo salvo, mas o e-mail ao PCM falhou: {exc}")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["motor_catalog_map"] = build_motor_catalog_map(self.get_area())
        context["current_motor_area"] = self.get_sidebar_area()
        context["can_send_pcm_from_form"] = not getattr(self, "object", None) or not self.object.pcm_email_sent
        return context


class BurnedMotorCaseCreateView(AppPermissionRequiredMixin, BurnedMotorCaseFormMixin, CreateView):
    model = BurnedMotorCase

    def form_valid(self, form):
        self.object = create_burned_case_from_form(form, area=self.get_area(), user=self.request.user)
        self._handle_pcm_email(self.object)
        messages.success(self.request, "Processo de motor queimado aberto com sucesso.")
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse("motores:burned-case-detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Novo processo de motor queimado"
        context["submit_label"] = "Abrir processo"
        return context


class BurnedMotorCaseDetailView(AppPermissionRequiredMixin, BurnedMotorCaseObjectMixin, DetailView):
    template_name = "motores/burned_cases/detail.html"
    permission_required = PermissionName.MANAGE_AREA_DATA

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = self.object.process_code
        context["timeline_events"] = build_case_timeline(self.object)
        context["status_form"] = BurnedMotorCaseStatusForm(initial={"status": self.object.status})
        context["can_send_pcm_email"] = self.object.needs_pcm and not self.object.pcm_email_sent
        return context


class BurnedMotorCaseUpdateView(AppPermissionRequiredMixin, BurnedMotorCaseObjectMixin, BurnedMotorCaseFormMixin, UpdateView):
    model = BurnedMotorCase

    def form_valid(self, form):
        self.object = update_burned_case_from_form(form, area=self.get_area(), user=self.request.user)
        self._handle_pcm_email(self.object)
        messages.success(self.request, "Processo de motor queimado atualizado com sucesso.")
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse("motores:burned-case-detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Editar {self.object.process_code}"
        context["submit_label"] = "Salvar processo"
        return context


class BurnedMotorCaseStatusUpdateView(AppPermissionRequiredMixin, BurnedMotorCaseObjectMixin, View):
    permission_required = PermissionName.MANAGE_AREA_DATA

    def post(self, request, *args, **kwargs):
        case = self.get_case()
        form = BurnedMotorCaseStatusForm(request.POST)
        if form.is_valid():
            update_burned_case_status(
                case,
                status=form.cleaned_data["status"],
                notes=form.cleaned_data["progress_notes"],
                user=request.user,
            )
            messages.success(request, "Status atualizado com sucesso.")
        else:
            messages.error(request, "Nao foi possivel atualizar o status do processo.")
        return HttpResponseRedirect(reverse("motores:burned-case-detail", kwargs={"pk": case.pk}))


class BurnedMotorCaseSendPCMEmailView(AppPermissionRequiredMixin, BurnedMotorCaseObjectMixin, View):
    permission_required = PermissionName.MANAGE_AREA_DATA

    def post(self, request, *args, **kwargs):
        case = self.get_case()
        try:
            send_burned_case_pcm_email(case, actor=request.user)
            messages.success(request, "E-mail enviado ao PCM com sucesso.")
        except PCMNotificationError as exc:
            messages.error(request, str(exc))
        return HttpResponseRedirect(reverse("motores:burned-case-detail", kwargs={"pk": case.pk}))


class BurnedMotorProcessCreateView(AppPermissionRequiredMixin, MotorAreaMixin, CreateView):
    template_name = "motores/flow_form.html"
    form_class = BurnedMotorProcessForm
    permission_required = PermissionName.MANAGE_AREA_DATA

    def dispatch(self, request, *args, **kwargs):
        self.motor = get_object_or_404(ElectricMotor.objects.select_related("area"), pk=kwargs["motor_pk"])
        ensure_area_access(request.user, self.motor.area)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = create_burned_process_from_form(form, motor=self.motor, user=self.request.user)
        messages.success(self.request, "Fluxo legado de motor queimado registrado com sucesso.")
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse("motores:detail", kwargs={"pk": self.motor.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["motor"] = self.motor
        context["page_title"] = f"Novo fluxo legado - {self.motor.mo}"
        context["submit_label"] = "Registrar fluxo"
        return context


class BurnedMotorProcessUpdateView(AppPermissionRequiredMixin, MotorAreaMixin, UpdateView):
    template_name = "motores/flow_form.html"
    form_class = BurnedMotorProcessForm
    model = BurnedMotorProcess
    context_object_name = "process"
    pk_url_kwarg = "process_pk"
    permission_required = PermissionName.MANAGE_AREA_DATA

    def dispatch(self, request, *args, **kwargs):
        self.motor = get_object_or_404(ElectricMotor.objects.select_related("area"), pk=kwargs["motor_pk"])
        ensure_area_access(request.user, self.motor.area)
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return BurnedMotorProcess.objects.select_related("motor", "registered_by_user", "updated_by_user").filter(motor=self.motor)

    def form_valid(self, form):
        self.object = update_burned_process_from_form(form, user=self.request.user)
        messages.success(self.request, "Fluxo legado de motor queimado atualizado com sucesso.")
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse("motores:detail", kwargs={"pk": self.motor.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["motor"] = self.motor
        context["page_title"] = f"Editar fluxo legado - {self.motor.mo}"
        context["submit_label"] = "Salvar fluxo"
        return context
