from __future__ import annotations

from decimal import Decimal
from urllib.parse import urlencode

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core.mail import EmailMultiAlternatives
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.template.loader import render_to_string
from django.utils import timezone

from apps.motores.models import BurnedMotorCase, BurnedMotorCaseEvent, BurnedMotorProcess, ElectricMotor
from apps.unidades.models import Area
from apps.unidades.services import build_lookup_exact_q, build_user_unidade_scope_q
from common.enums import (
    AreaCode,
    BurnedMotorCaseStatus,
    MotorBurnoutFlowStatus,
    MotorDataOrigin,
    MotorStatus,
)
from common.permissions import PermissionName, ensure_area_access, get_allowed_areas, has_permission, is_global_user


FINAL_BURNED_CASE_STATUSES = {
    BurnedMotorCaseStatus.RECEIVED,
    BurnedMotorCaseStatus.COMPLETED,
    BurnedMotorCaseStatus.CANCELLED,
}
PCM_STAGE_STATUSES = {
    BurnedMotorCaseStatus.AWAITING_PCM,
    BurnedMotorCaseStatus.SENT_TO_PCM,
    BurnedMotorCaseStatus.PCM_ANALYSIS,
}
PCM_MILESTONE_STATUSES = PCM_STAGE_STATUSES | {
    BurnedMotorCaseStatus.SENT_TO_FINANCE,
    BurnedMotorCaseStatus.AWAITING_APPROVAL,
    BurnedMotorCaseStatus.APPROVED,
    BurnedMotorCaseStatus.AWAITING_VENDOR,
    BurnedMotorCaseStatus.AWAITING_FREIGHT,
    BurnedMotorCaseStatus.IN_TRANSPORT,
    BurnedMotorCaseStatus.IN_REWINDING,
    BurnedMotorCaseStatus.AWAITING_RETURN,
    BurnedMotorCaseStatus.RECEIVED,
    BurnedMotorCaseStatus.COMPLETED,
}
FINANCE_MILESTONE_STATUSES = {
    BurnedMotorCaseStatus.SENT_TO_FINANCE,
    BurnedMotorCaseStatus.AWAITING_APPROVAL,
    BurnedMotorCaseStatus.APPROVED,
    BurnedMotorCaseStatus.AWAITING_VENDOR,
    BurnedMotorCaseStatus.AWAITING_FREIGHT,
    BurnedMotorCaseStatus.IN_TRANSPORT,
    BurnedMotorCaseStatus.IN_REWINDING,
    BurnedMotorCaseStatus.AWAITING_RETURN,
    BurnedMotorCaseStatus.RECEIVED,
    BurnedMotorCaseStatus.COMPLETED,
}
APPROVAL_MILESTONE_STATUSES = {
    BurnedMotorCaseStatus.APPROVED,
    BurnedMotorCaseStatus.AWAITING_VENDOR,
    BurnedMotorCaseStatus.AWAITING_FREIGHT,
    BurnedMotorCaseStatus.IN_TRANSPORT,
    BurnedMotorCaseStatus.IN_REWINDING,
    BurnedMotorCaseStatus.AWAITING_RETURN,
    BurnedMotorCaseStatus.RECEIVED,
    BurnedMotorCaseStatus.COMPLETED,
}
ARRIVAL_MILESTONE_STATUSES = {
    BurnedMotorCaseStatus.RECEIVED,
    BurnedMotorCaseStatus.COMPLETED,
}
PROVISIONAL_REQUIRED_FIELDS = (
    "motor_description",
    "motor_power",
    "motor_manufacturer",
    "motor_frame",
    "motor_rpm",
    "motor_voltage",
    "motor_current",
)
CASE_STAGE_FILTERS = {
    "pcm": Q(status__in=[BurnedMotorCaseStatus.AWAITING_PCM, BurnedMotorCaseStatus.SENT_TO_PCM, BurnedMotorCaseStatus.PCM_ANALYSIS])
    | Q(sent_to_pcm=True),
    "financeiro": Q(status__in=[BurnedMotorCaseStatus.SENT_TO_FINANCE, BurnedMotorCaseStatus.AWAITING_APPROVAL, BurnedMotorCaseStatus.APPROVED])
    | Q(sent_to_finance=True)
    | Q(approved=True),
    "terceiro": Q(status__in=[BurnedMotorCaseStatus.AWAITING_VENDOR, BurnedMotorCaseStatus.IN_REWINDING, BurnedMotorCaseStatus.AWAITING_RETURN])
    | ~Q(third_party_company=""),
    "frete": Q(status__in=[BurnedMotorCaseStatus.AWAITING_FREIGHT, BurnedMotorCaseStatus.IN_TRANSPORT]) | Q(freight_requested=True),
    "retorno": Q(status__in=[BurnedMotorCaseStatus.AWAITING_RETURN, BurnedMotorCaseStatus.RECEIVED]) | Q(arrived_at__isnull=False),
}


class PCMNotificationError(RuntimeError):
    pass


def motor_unidade_lookup_paths() -> tuple[str, ...]:
    return ("unidade_id",)


def motor_fabrica_lookup_paths() -> tuple[str, ...]:
    return ("unidade__fabrica__code",)


def burned_case_unidade_lookup_paths() -> tuple[str, ...]:
    return ("unidade_id", "motor__unidade_id")


def burned_case_fabrica_lookup_paths() -> tuple[str, ...]:
    return ("unidade__fabrica__code", "motor__unidade__fabrica__code")


def resolve_motor_area(user, area_code: str | None):
    area = None
    if area_code:
        area = Area.objects.filter(code=area_code).first()
        ensure_area_access(user, area)
    else:
        area = getattr(user, "area", None)
        if area is None or area.code != AreaCode.ELETRICA:
            area = next(
                (
                    allowed_area
                    for allowed_area in get_allowed_areas(user)
                    if allowed_area is not None and allowed_area.code == AreaCode.ELETRICA
                ),
                area,
            )
        if area is not None:
            ensure_area_access(user, area)
    if area is None or area.code != AreaCode.ELETRICA:
        raise PermissionDenied("Modulo de motores eletricos disponivel apenas para a area Eletrica.")
    return area


def serialize_query_without_page(querydict) -> str:
    data = querydict.copy()
    if "page" in data:
        data.pop("page")
    return urlencode(data, doseq=True)


def paginate_queryset(queryset, page_number: str | int | None, per_page: int = 12):
    return Paginator(queryset, per_page).get_page(page_number)


def base_motor_queryset(user, *, area):
    queryset = ElectricMotor.objects.select_related(
        "area",
        "unidade",
        "unidade__fabrica",
        "registered_by_user",
    ).order_by("mo")
    if not is_global_user(user):
        allowed_areas = get_allowed_areas(user)
        if not allowed_areas:
            return queryset.none()
        queryset = queryset.filter(area=area, area__in=allowed_areas)
    else:
        queryset = queryset.filter(area=area)

    return queryset.filter(
        build_user_unidade_scope_q(
            user,
            motor_unidade_lookup_paths(),
            include_unassigned_for_broad_scope=True,
        )
    ).distinct()


def apply_motor_filters(queryset, cleaned_data: dict):
    search = cleaned_data.get("search")
    manufacturer = cleaned_data.get("manufacturer")
    fabrica_code = cleaned_data.get("fabrica")
    unidade_id = cleaned_data.get("unidade")
    status = cleaned_data.get("status")

    if search:
        queryset = queryset.filter(
            Q(mo__icontains=search)
            | Q(power__icontains=search)
            | Q(frame__icontains=search)
            | Q(manufacturer__icontains=search)
            | Q(description__icontains=search)
            | Q(location_name__icontains=search)
            | Q(unidade__name__icontains=search)
            | Q(unidade__fabrica__name__icontains=search)
        )
    if manufacturer:
        queryset = queryset.filter(manufacturer__icontains=manufacturer)
    if fabrica_code:
        queryset = queryset.filter(build_lookup_exact_q(motor_fabrica_lookup_paths(), fabrica_code))
    if unidade_id:
        queryset = queryset.filter(build_lookup_exact_q(motor_unidade_lookup_paths(), unidade_id))
    if status:
        queryset = queryset.filter(status=status)
    return queryset.distinct()


def paginate_motor_queryset(queryset, page_number: str | int | None, per_page: int = 12):
    return paginate_queryset(queryset, page_number, per_page=per_page)


def can_manage_motor_registry(user) -> bool:
    return has_permission(user, PermissionName.MANAGE_AREA_DATA)


def can_manage_burned_motor_flow(user) -> bool:
    return has_permission(user, PermissionName.MANAGE_AREA_DATA)


def create_motor_from_form(form, *, area, user):
    motor = form.save(commit=False)
    motor.area = area
    motor.registered_by_user = user
    if not motor.registered_at:
        motor.registered_at = timezone.now()
    if not motor.unidade_id:
        raise ValueError("Selecione a unidade produtiva do motor.")
    motor.save()
    return motor


def update_motor_from_form(form):
    motor = form.save(commit=False)
    if not motor.unidade_id:
        raise ValueError("Selecione a unidade produtiva do motor.")
    motor.save()
    return motor


def motor_snapshot_from_catalog(motor: ElectricMotor) -> dict:
    return {
        "unidade": str(motor.unidade_id) if motor.unidade_id else "",
        "motor_description": motor.description or motor.mo,
        "motor_mo": motor.mo,
        "motor_power": motor.power,
        "motor_manufacturer": motor.manufacturer,
        "motor_frame": motor.frame,
        "motor_rpm": motor.rpm,
        "motor_voltage": str(motor.voltage) if motor.voltage is not None else "",
        "motor_current": str(motor.current) if motor.current is not None else "",
        "motor_location": motor.location_name or "",
    }


def build_motor_catalog_map(area):
    snapshot_map: dict[str, dict] = {}
    for motor in ElectricMotor.objects.select_related("unidade", "unidade__fabrica").filter(area=area).order_by("mo"):
        snapshot_map[str(motor.pk)] = motor_snapshot_from_catalog(motor)
    return snapshot_map


def _normalize_process_dates(process: BurnedMotorProcess):
    now = timezone.now()
    if process.sent_to_pcm and not process.sent_to_pcm_at:
        process.sent_to_pcm_at = now
    if not process.sent_to_pcm:
        process.sent_to_pcm_at = None

    if process.payment_approved and not process.approved_at:
        process.approved_at = now
    if not process.payment_approved:
        process.approved_at = None

    if process.arrived and not process.arrived_at:
        process.arrived_at = now
    if not process.arrived:
        process.arrived_at = None


def create_burned_process_from_form(form, *, motor, user):
    process = form.save(commit=False)
    process.motor = motor
    process.registered_by_user = user
    process.updated_by_user = user
    _normalize_process_dates(process)
    process.save()
    return process


def update_burned_process_from_form(form, *, user):
    process = form.save(commit=False)
    process.updated_by_user = user
    _normalize_process_dates(process)
    process.save()
    return process


def build_motor_flow_summary(motor):
    cases = motor.burned_cases.order_by("-occurred_at", "-created_at")
    return {
        "total_processes": cases.count(),
        "open_processes": cases.exclude(status__in=FINAL_BURNED_CASE_STATUSES).count(),
        "completed_processes": cases.filter(status=BurnedMotorCaseStatus.COMPLETED).count(),
        "last_status": cases.first().get_status_display() if cases.exists() else "Sem processo registrado",
    }


def build_motor_history(motor):
    events = [
        {
            "title": "Motor cadastrado",
            "timestamp": motor.registered_at,
            "subtitle": motor.registered_by_user.full_name if motor.registered_by_user else "Cadastro sem responsavel",
        }
    ]
    for case in motor.burned_cases.order_by("-occurred_at", "-created_at")[:10]:
        events.append(
            {
                "title": case.get_status_display(),
                "timestamp": case.updated_at,
                "subtitle": case.problem_type or case.process_code,
            }
        )
    return sorted(events, key=lambda item: item["timestamp"], reverse=True)


def related_burned_cases_queryset(motor):
    return motor.burned_cases.select_related(
        "opened_by_user",
        "updated_by_user",
        "unidade",
        "unidade__fabrica",
    ).order_by("-occurred_at", "-updated_at")


def base_burned_case_queryset(user, *, area):
    queryset = BurnedMotorCase.objects.select_related(
        "motor",
        "motor__unidade",
        "motor__unidade__fabrica",
        "opened_by_user",
        "updated_by_user",
        "area",
        "unidade",
        "unidade__fabrica",
    ).order_by("-occurred_at", "-updated_at")
    if not is_global_user(user):
        allowed_areas = get_allowed_areas(user)
        if not allowed_areas:
            return queryset.none()
        queryset = queryset.filter(area=area, area__in=allowed_areas)
    else:
        queryset = queryset.filter(area=area)

    return queryset.filter(
        build_user_unidade_scope_q(
            user,
            burned_case_unidade_lookup_paths(),
            include_unassigned_for_broad_scope=True,
        )
    ).distinct()


def apply_burned_case_filters(queryset, cleaned_data: dict):
    search = cleaned_data.get("search")
    status = cleaned_data.get("status")
    process_stage = cleaned_data.get("process_stage")
    fabrica_code = cleaned_data.get("fabrica")
    unidade_id = cleaned_data.get("unidade")
    location = cleaned_data.get("location")
    start_date = cleaned_data.get("start_date")
    end_date = cleaned_data.get("end_date")

    if search:
        queryset = queryset.filter(
            Q(process_code__icontains=search)
            | Q(motor_description__icontains=search)
            | Q(motor_mo__icontains=search)
            | Q(motor__mo__icontains=search)
            | Q(requester_name__icontains=search)
            | Q(problem_type__icontains=search)
            | Q(third_party_company__icontains=search)
            | Q(unidade__name__icontains=search)
            | Q(unidade__fabrica__name__icontains=search)
        )
    if status:
        queryset = queryset.filter(status=status)
    if process_stage:
        queryset = queryset.filter(CASE_STAGE_FILTERS.get(process_stage, Q()))
    if fabrica_code:
        queryset = queryset.filter(build_lookup_exact_q(burned_case_fabrica_lookup_paths(), fabrica_code))
    if unidade_id:
        queryset = queryset.filter(build_lookup_exact_q(burned_case_unidade_lookup_paths(), unidade_id))
    if location:
        queryset = queryset.filter(motor_location__icontains=location)
    if start_date:
        queryset = queryset.filter(occurred_at__date__gte=start_date)
    if end_date:
        queryset = queryset.filter(occurred_at__date__lte=end_date)
    return queryset.distinct()


def paginate_burned_case_queryset(queryset, page_number: str | int | None, per_page: int = 12):
    return paginate_queryset(queryset, page_number, per_page=per_page)


def build_burned_case_summary(queryset):
    open_queryset = queryset.exclude(status__in=FINAL_BURNED_CASE_STATUSES)
    return {
        "open_count": open_queryset.count(),
        "overdue_count": open_queryset.filter(expected_return_at__lt=timezone.now()).count(),
        "awaiting_pcm_count": queryset.filter(
            status__in=[
                BurnedMotorCaseStatus.OPEN,
                BurnedMotorCaseStatus.IDENTIFIED,
                BurnedMotorCaseStatus.AWAITING_PCM,
            ]
        ).count(),
        "awaiting_finance_count": queryset.filter(
            status__in=[
                BurnedMotorCaseStatus.SENT_TO_FINANCE,
                BurnedMotorCaseStatus.AWAITING_APPROVAL,
            ]
        ).count(),
    }


def _format_bool(value) -> str:
    return "Sim" if value else "Nao"


def _add_form_error(errors: dict[str, list[str]], field_name: str, message: str):
    errors.setdefault(field_name, []).append(message)


def validate_burned_case_form_data(cleaned_data: dict) -> dict[str, list[str]]:
    errors: dict[str, list[str]] = {}

    motor_lookup = cleaned_data.get("motor_lookup")
    create_provisional_motor = cleaned_data.get("create_provisional_motor")
    needs_pcm = cleaned_data.get("needs_pcm")
    sent_to_pcm = cleaned_data.get("sent_to_pcm")
    sent_to_pcm_at = cleaned_data.get("sent_to_pcm_at")
    sent_to_finance = cleaned_data.get("sent_to_finance")
    finance_sent_at = cleaned_data.get("finance_sent_at")
    approved = cleaned_data.get("approved")
    approved_at = cleaned_data.get("approved_at")
    status = cleaned_data.get("status")

    if not motor_lookup and not (cleaned_data.get("motor_description") or cleaned_data.get("motor_mo")):
        _add_form_error(
            errors,
            "motor_description",
            "Selecione um motor cadastrado ou informe manualmente a identificacao do motor.",
        )

    if create_provisional_motor and motor_lookup:
        _add_form_error(
            errors,
            "create_provisional_motor",
            "Remova o motor selecionado para criar um cadastro provisÃ³rio.",
        )

    if create_provisional_motor:
        for field_name in PROVISIONAL_REQUIRED_FIELDS:
            if not cleaned_data.get(field_name):
                _add_form_error(
                    errors,
                    field_name,
                    "Preencha este campo para criar um cadastro provisÃ³rio.",
                )

    if sent_to_pcm_at and not sent_to_pcm:
        _add_form_error(errors, "sent_to_pcm", "Marque o envio ao PCM quando houver data informada.")

    if finance_sent_at and not sent_to_finance:
        _add_form_error(errors, "sent_to_finance", "Marque o envio ao financeiro quando houver data informada.")

    if approved_at and not approved:
        _add_form_error(errors, "approved", "Marque a aprovacao quando houver data informada.")

    if not needs_pcm and (sent_to_pcm or sent_to_pcm_at or cleaned_data.get("pcm_responsible")):
        _add_form_error(errors, "needs_pcm", "Mantenha esta opcao marcada se o fluxo passar pelo PCM.")

    if not needs_pcm and status in PCM_STAGE_STATUSES:
        _add_form_error(errors, "status", "Este status exige fluxo passando pelo PCM.")

    return errors


def _normalize_case_flags(case: BurnedMotorCase):
    now = timezone.now()
    if case.sent_to_pcm and not case.sent_to_pcm_at:
        case.sent_to_pcm_at = now
    if not case.sent_to_pcm:
        case.sent_to_pcm_at = None

    if case.sent_to_finance and not case.finance_sent_at:
        case.finance_sent_at = now
    if not case.sent_to_finance:
        case.finance_sent_at = None

    if case.approved and not case.approved_at:
        case.approved_at = now
    if not case.approved:
        case.approved_at = None


def _apply_case_milestones_from_status(case: BurnedMotorCase):
    now = timezone.now()

    if case.status in PCM_MILESTONE_STATUSES:
        case.sent_to_pcm = True
        case.sent_to_pcm_at = case.sent_to_pcm_at or now

    if case.status in FINANCE_MILESTONE_STATUSES:
        case.sent_to_finance = True
        case.finance_sent_at = case.finance_sent_at or now

    if case.status in APPROVAL_MILESTONE_STATUSES:
        case.approved = True
        case.approved_at = case.approved_at or now

    if case.status in ARRIVAL_MILESTONE_STATUSES:
        case.arrived_at = case.arrived_at or now


def create_case_event(case: BurnedMotorCase, *, actor, title: str, details: str = "", event_type: str = "note"):
    return BurnedMotorCaseEvent.objects.create(
        case=case,
        actor_user=actor,
        title=title,
        details=details,
        event_type=event_type,
        event_at=timezone.now(),
    )


def _generate_unique_provisional_mo(base_code: str) -> str:
    candidate = base_code
    counter = 1
    while ElectricMotor.objects.filter(mo=candidate).exists():
        candidate = f"{base_code}-{counter}"
        counter += 1
    return candidate


def create_provisional_motor_from_case(case: BurnedMotorCase, *, user):
    base_code = case.motor_mo or f"PROV-{case.process_code}"
    generated_mo = _generate_unique_provisional_mo(base_code.upper())
    notes = [f"Cadastro provisÃ³rio criado a partir do processo {case.process_code}."]
    if case.motor_location:
        notes.append(f"Local informado: {case.motor_location}.")
    if case.technical_notes:
        notes.append(case.technical_notes)
    provisional_motor = ElectricMotor.objects.create(
        area=case.area,
        unidade=case.unidade,
        mo=generated_mo,
        description=case.motor_description or case.motor_mo or f"Motor provisÃ³rio {case.process_code}",
        power=case.motor_power,
        manufacturer=case.motor_manufacturer,
        frame=case.motor_frame,
        rpm=case.motor_rpm,
        voltage=case.motor_voltage or Decimal("0"),
        current=case.motor_current or Decimal("0"),
        location_name=case.motor_location or "",
        is_provisional=True,
        status=MotorStatus.INTERNAL_MAINTENANCE,
        notes="\n".join(notes),
        registered_by_user=user,
    )
    case.motor = provisional_motor
    case.data_origin = MotorDataOrigin.PROVISIONAL
    case.save(update_fields=["motor", "data_origin", "updated_at"])
    create_case_event(
        case,
        actor=user,
        title="Cadastro provisÃ³rio criado",
        details=f"Motor provisÃ³rio {provisional_motor.mo} vinculado ao processo.",
        event_type="provisional_motor",
    )
    return provisional_motor


def _populate_case_from_form(case: BurnedMotorCase, *, form, area, user):
    selected_motor = form.cleaned_data.get("motor_lookup")
    selected_unidade = form.cleaned_data.get("unidade")
    create_provisional_motor = form.cleaned_data.get("create_provisional_motor")

    case.area = area
    case.motor = selected_motor
    case.unidade = selected_motor.unidade if selected_motor and selected_motor.unidade_id else selected_unidade
    case.updated_by_user = user
    if not case.pk:
        case.opened_by_user = user
        if not case.recorded_at:
            case.recorded_at = timezone.now()

    if selected_motor is not None:
        case.data_origin = MotorDataOrigin.CATALOG
        snapshot = motor_snapshot_from_catalog(selected_motor)
        if not case.unidade_id and snapshot.get("unidade"):
            case.unidade_id = snapshot["unidade"]
        for field_name, field_value in snapshot.items():
            if field_name == "unidade":
                continue
            if not getattr(case, field_name):
                setattr(case, field_name, field_value)
    else:
        case.data_origin = MotorDataOrigin.PROVISIONAL if create_provisional_motor else MotorDataOrigin.MANUAL

    _normalize_case_flags(case)
    _apply_case_milestones_from_status(case)
    return selected_motor, create_provisional_motor


def create_burned_case_from_form(form, *, area, user):
    with transaction.atomic():
        case = form.save(commit=False)
        selected_motor, create_provisional_motor = _populate_case_from_form(case, form=form, area=area, user=user)
        case.save()

        if selected_motor is not None:
            create_case_event(
                case,
                actor=user,
                title="Processo aberto",
                details=f"Processo vinculado ao motor cadastrado {selected_motor.mo}.",
                event_type="created",
            )
        else:
            create_case_event(
                case,
                actor=user,
                title="Processo aberto",
                details="Processo aberto com dados informados manualmente.",
                event_type="created",
            )

        if create_provisional_motor and selected_motor is None:
            create_provisional_motor_from_case(case, user=user)

    return case


def update_burned_case_from_form(form, *, area, user):
    with transaction.atomic():
        case = form.save(commit=False)
        previous_status = form.instance.status
        previous_motor_id = form.instance.motor_id
        selected_motor, create_provisional_motor = _populate_case_from_form(case, form=form, area=area, user=user)
        case.save()

        if create_provisional_motor and selected_motor is None and case.motor_id is None:
            create_provisional_motor_from_case(case, user=user)

        if case.status != previous_status:
            create_case_event(
                case,
                actor=user,
                title=f"Status alterado para {case.get_status_display()}",
                details=case.progress_notes or "",
                event_type="status",
            )
        elif previous_motor_id != case.motor_id and case.motor_id:
            create_case_event(
                case,
                actor=user,
                title="Motor vinculado ao processo",
                details=f"Motor {case.motor.mo} associado ao processo.",
                event_type="motor_linked",
            )
        else:
            create_case_event(
                case,
                actor=user,
                title="Processo atualizado",
                details=case.progress_notes or "",
                event_type="updated",
            )

    return case


def update_burned_case_status(case: BurnedMotorCase, *, status: str, notes: str, user):
    with transaction.atomic():
        case.status = status
        case.updated_by_user = user
        _apply_case_milestones_from_status(case)
        case.save(
            update_fields=[
                "status",
                "sent_to_pcm",
                "sent_to_pcm_at",
                "sent_to_finance",
                "finance_sent_at",
                "approved",
                "approved_at",
                "arrived_at",
                "updated_by_user",
                "updated_at",
            ]
        )
        create_case_event(
            case,
            actor=user,
            title=f"Status alterado para {case.get_status_display()}",
            details=notes,
            event_type="status",
        )
    return case


def build_pcm_email_subject(case: BurnedMotorCase) -> str:
    return render_to_string(
        "motores/burned_cases/emails/pcm_subject.txt",
        {"case": case},
    ).strip()


def build_pcm_email_context(case: BurnedMotorCase) -> dict:
    unidade = case.resolved_unidade
    fabrica = case.resolved_fabrica
    return {
        "case": case,
        "motor_label": case.display_motor_label,
        "location_label": case.motor_location or (unidade.name if unidade is not None else case.area.name),
        "opened_by_label": case.opened_by_user.full_name if case.opened_by_user else "-",
        "unidade_label": unidade.name if unidade is not None else "-",
        "fabrica_label": fabrica.name if fabrica is not None else "-",
    }


def build_pcm_email_content(case: BurnedMotorCase) -> tuple[str, str]:
    context = build_pcm_email_context(case)
    text_body = render_to_string("motores/burned_cases/emails/pcm_body.txt", context).strip()
    html_body = render_to_string("motores/burned_cases/emails/pcm_body.html", context).strip()
    return text_body, html_body


def get_pcm_notification_recipients() -> list[str]:
    return list(getattr(settings, "PCM_NOTIFICATION_EMAILS", []))


def send_burned_case_pcm_email(case: BurnedMotorCase, *, actor):
    recipients = get_pcm_notification_recipients()
    if not recipients:
        raise PCMNotificationError("Nao ha destinatario configurado para notificacoes do PCM.")

    text_body, html_body = build_pcm_email_content(case)
    message = EmailMultiAlternatives(
        subject=build_pcm_email_subject(case),
        body=text_body,
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", settings.DEFAULT_ADMIN_EMAIL),
        to=recipients,
    )
    message.attach_alternative(html_body, "text/html")

    try:
        sent_count = message.send(fail_silently=False)
    except Exception as exc:  # noqa: BLE001
        raise PCMNotificationError(f"Nao foi possivel enviar o e-mail ao PCM: {exc}") from exc

    if sent_count:
        with transaction.atomic():
            now = timezone.now()
            case.pcm_email_sent = True
            case.pcm_email_sent_at = now
            case.sent_to_pcm = True
            if not case.sent_to_pcm_at:
                case.sent_to_pcm_at = now
            if case.status in {
                BurnedMotorCaseStatus.OPEN,
                BurnedMotorCaseStatus.IDENTIFIED,
                BurnedMotorCaseStatus.AWAITING_PCM,
            }:
                case.status = BurnedMotorCaseStatus.SENT_TO_PCM
            case.updated_by_user = actor
            case.save(
                update_fields=[
                    "pcm_email_sent",
                    "pcm_email_sent_at",
                    "sent_to_pcm",
                    "sent_to_pcm_at",
                    "status",
                    "updated_by_user",
                    "updated_at",
                ]
            )
            create_case_event(
                case,
                actor=actor,
                title="E-mail enviado ao PCM",
                details=f"E-mail operacional enviado para: {', '.join(recipients)}",
                event_type="pcm_email",
            )
    return sent_count


def build_case_timeline(case: BurnedMotorCase):
    return case.events.select_related("actor_user").order_by("-event_at", "-created_at")
