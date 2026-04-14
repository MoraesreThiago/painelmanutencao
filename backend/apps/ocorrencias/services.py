from __future__ import annotations

from urllib.parse import urlencode

from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.auditoria.services import audit_logs_for_entity, base_audit_queryset, register_audit_event
from apps.integracoes.services import enqueue_sync_item
from apps.ocorrencias.models import BurnedMotorRecord, InstrumentServiceRequest, Movement, Occurrence
from apps.unidades.models import Area
from apps.unidades.services import build_lookup_exact_q, build_user_unidade_scope_q
from common.enums import EquipmentStatus, OccurrenceStatus
from common.permissions import ensure_area_access, get_allowed_areas, is_global_user


ACTIVE_OCCURRENCE_STATUSES = {
    OccurrenceStatus.OPEN,
    OccurrenceStatus.IN_PROGRESS,
    OccurrenceStatus.WAITING_PARTS,
}
HISTORY_ACTION_CHOICES = (
    ("", "Todas as acoes"),
    ("created", "Criacao"),
    ("updated", "Edicao"),
    ("status_changed", "Mudanca de status"),
)


def occurrence_unidade_lookup_paths() -> tuple[str, ...]:
    return (
        "unidade_id",
        "location__unidade_id",
        "equipment__unidade_id",
        "equipment__location__unidade_id",
    )


def occurrence_fabrica_lookup_paths() -> tuple[str, ...]:
    return (
        "unidade__fabrica__code",
        "location__unidade__fabrica__code",
        "equipment__unidade__fabrica__code",
        "equipment__location__unidade__fabrica__code",
    )


def build_occurrence_physical_scope_q(user) -> Q:
    return build_user_unidade_scope_q(
        user,
        occurrence_unidade_lookup_paths(),
        include_unassigned_for_broad_scope=True,
    )


def recent_occurrence_feed(area=None):
    occurrences = Occurrence.objects.select_related("equipment", "reported_by_user").order_by("-occurred_at")
    movements = Movement.objects.select_related("equipment", "moved_by_user").order_by("-moved_at")
    burned = BurnedMotorRecord.objects.select_related("motor", "recorded_by_user").order_by("-recorded_at")
    service_requests = InstrumentServiceRequest.objects.select_related("instrument", "registered_by_user").order_by(
        "-requested_at"
    )
    if area is not None:
        occurrences = occurrences.filter(area=area)
        movements = movements.filter(equipment__area=area)
        burned = burned.filter(area=area)
        service_requests = service_requests.filter(area=area)
    return {
        "occurrences": occurrences[:10],
        "movements": movements[:10],
        "burned_motors": burned[:10],
        "instrument_requests": service_requests[:10],
    }


def base_occurrence_queryset(user):
    queryset = Occurrence.objects.select_related(
        "equipment",
        "equipment__unidade",
        "equipment__unidade__fabrica",
        "equipment__location",
        "equipment__location__unidade",
        "equipment__location__unidade__fabrica",
        "area",
        "location",
        "location__unidade",
        "location__unidade__fabrica",
        "unidade",
        "unidade__fabrica",
        "responsible_collaborator",
        "reported_by_user",
    ).order_by("-occurred_at", "-created_at")
    if not is_global_user(user):
        allowed_areas = get_allowed_areas(user)
        if not allowed_areas:
            return queryset.none()
        queryset = queryset.filter(area__in=allowed_areas)

    return queryset.filter(build_occurrence_physical_scope_q(user)).distinct()


def resolve_area_from_code(user, area_code: str | None):
    if not area_code:
        return None
    area = Area.objects.filter(code=area_code).first()
    ensure_area_access(user, area)
    return area


def apply_occurrence_filters(queryset, cleaned_data: dict):
    search = cleaned_data.get("search")
    area_code = cleaned_data.get("area")
    fabrica_code = cleaned_data.get("fabrica")
    unidade_id = cleaned_data.get("unidade")
    location_id = cleaned_data.get("location")
    classification = cleaned_data.get("classification")
    status = cleaned_data.get("status")
    downtime = cleaned_data.get("downtime")

    if search:
        queryset = queryset.filter(
            Q(description__icontains=search)
            | Q(notes__icontains=search)
            | Q(equipment__code__icontains=search)
            | Q(equipment__tag__icontains=search)
            | Q(equipment__description__icontains=search)
            | Q(location__name__icontains=search)
            | Q(unidade__name__icontains=search)
            | Q(unidade__fabrica__name__icontains=search)
            | Q(responsible_collaborator__full_name__icontains=search)
        )
    if area_code:
        queryset = queryset.filter(area__code=area_code)
    if fabrica_code:
        queryset = queryset.filter(build_lookup_exact_q(occurrence_fabrica_lookup_paths(), fabrica_code))
    if unidade_id:
        queryset = queryset.filter(build_lookup_exact_q(occurrence_unidade_lookup_paths(), unidade_id))
    if location_id:
        queryset = queryset.filter(location_id=location_id)
    if classification:
        queryset = queryset.filter(classification=classification)
    if status:
        queryset = queryset.filter(status=status)
    if downtime == "yes":
        queryset = queryset.filter(had_downtime=True)
    elif downtime == "no":
        queryset = queryset.filter(had_downtime=False)
    return queryset.distinct()


def paginate_occurrence_queryset(queryset, page_number: str | int | None, per_page: int = 12):
    return Paginator(queryset, per_page).get_page(page_number)


def paginate_history_queryset(queryset, page_number: str | int | None, per_page: int = 14):
    return Paginator(queryset, per_page).get_page(page_number)


def serialize_query_without_page(querydict) -> str:
    data = querydict.copy()
    if "page" in data:
        data.pop("page")
    return urlencode(data, doseq=True)


def build_occurrence_timeline(occurrence: Occurrence):
    return audit_logs_for_entity(entity_name="Occurrence", entity_id=str(occurrence.id)).order_by("-created_at")


def recent_occurrences_for_equipment(equipment, *, limit: int = 5):
    return (
        equipment.occurrences.select_related("reported_by_user", "responsible_collaborator")
        .order_by("-occurred_at", "-created_at")[:limit]
    )


def build_occurrence_history_queryset(user):
    queryset = base_audit_queryset().filter(entity_name="Occurrence")
    if is_global_user(user):
        return queryset

    allowed_areas = get_allowed_areas(user)
    if allowed_areas:
        return queryset.filter(area__in=allowed_areas)
    return queryset.none()


def apply_history_filters(queryset, cleaned_data: dict):
    search = cleaned_data.get("search")
    area_code = cleaned_data.get("area")
    action = cleaned_data.get("action")

    if search:
        queryset = queryset.filter(
            Q(summary__icontains=search)
            | Q(actor_user__full_name__icontains=search)
            | Q(entity_id__icontains=search)
        )
    if area_code:
        queryset = queryset.filter(area__code=area_code)
    if action:
        queryset = queryset.filter(action=action)
    return queryset


def create_occurrence_from_form(form, actor):
    with transaction.atomic():
        occurrence = form.save(commit=False)
        _prepare_occurrence_for_save(occurrence, actor=actor, is_new=True)
        occurrence.save()
        _finalize_created_occurrence(occurrence, actor)
        return occurrence


def update_occurrence_from_form(form, actor):
    with transaction.atomic():
        previous = _snapshot_occurrence(form.instance)
        occurrence = form.save(commit=False)
        _prepare_occurrence_for_save(occurrence, actor=actor, is_new=False)
        occurrence.save()
        _finalize_updated_occurrence(
            occurrence,
            actor,
            previous=previous,
            changed_fields=form.changed_data,
        )
        return occurrence


def create_occurrence_from_api(validated_data: dict, actor):
    with transaction.atomic():
        occurrence = Occurrence(**validated_data)
        _prepare_occurrence_for_save(occurrence, actor=actor, is_new=True)
        occurrence.save()
        _finalize_created_occurrence(occurrence, actor)
        return occurrence


def update_occurrence_from_api(occurrence: Occurrence, validated_data: dict, actor):
    with transaction.atomic():
        previous = _snapshot_occurrence(occurrence)
        changed_fields = list(validated_data.keys())
        for field_name, value in validated_data.items():
            setattr(occurrence, field_name, value)
        _prepare_occurrence_for_save(occurrence, actor=actor, is_new=False)
        occurrence.save()
        _finalize_updated_occurrence(occurrence, actor, previous=previous, changed_fields=changed_fields)
        return occurrence


def update_occurrence_status(occurrence: Occurrence, *, status: str, actor, note: str = ""):
    with transaction.atomic():
        previous_status = occurrence.status
        occurrence.status = status
        _prepare_occurrence_for_save(occurrence, actor=actor, is_new=False)
        occurrence.save(update_fields=["status", "resolved_at", "area", "location", "unidade", "updated_at"])
        _sync_equipment_operational_status(occurrence.equipment)
        summary = f"Status da ocorrencia do equipamento {occurrence.equipment.code} alterado para {_status_label(occurrence.status)}."
        if note:
            summary = f"{summary} {note}"
        register_audit_event(
            actor_user=actor,
            entity_name="Occurrence",
            entity_id=str(occurrence.id),
            action="status_changed",
            area=occurrence.area,
            summary=summary,
            payload={
                **_occurrence_payload(occurrence),
                "previous_status": previous_status,
                "status_note": note,
            },
        )
        enqueue_sync_item(
            entity_name="Occurrence",
            entity_id=str(occurrence.id),
            action="status_changed",
            payload={"status": occurrence.status, "note": note},
        )
        return occurrence


def _prepare_occurrence_for_save(occurrence: Occurrence, *, actor, is_new: bool):
    occurrence.area = occurrence.equipment.area
    if occurrence.location_id and occurrence.location.area_id != occurrence.area_id:
        raise ValueError("A unidade/local precisa pertencer a mesma area do equipamento.")
    if not occurrence.location_id:
        occurrence.location = occurrence.equipment.location

    equipment_unidade = occurrence.equipment.resolved_unidade
    location_unidade = occurrence.location.unidade if occurrence.location_id and occurrence.location.unidade_id else None
    if equipment_unidade is not None and location_unidade is not None and equipment_unidade.id != location_unidade.id:
        raise ValueError("O local selecionado precisa pertencer a mesma unidade produtiva do equipamento.")

    occurrence.unidade = location_unidade or equipment_unidade

    if is_new and not occurrence.reported_by_user_id:
        occurrence.reported_by_user = actor
    if not occurrence.occurred_at:
        occurrence.occurred_at = timezone.now()
    if occurrence.had_downtime is False:
        occurrence.downtime_minutes = None
    if occurrence.status == OccurrenceStatus.RESOLVED:
        occurrence.resolved_at = occurrence.resolved_at or timezone.now()
    elif occurrence.status != OccurrenceStatus.CANCELLED:
        occurrence.resolved_at = None


def _finalize_created_occurrence(occurrence, actor):
    _sync_equipment_operational_status(occurrence.equipment)
    register_audit_event(
        actor_user=actor,
        entity_name="Occurrence",
        entity_id=str(occurrence.id),
        action="created",
        area=occurrence.area,
        summary=f"Ocorrencia registrada para o equipamento {occurrence.equipment.code}.",
        payload=_occurrence_payload(occurrence),
    )
    enqueue_sync_item(
        entity_name="Occurrence",
        entity_id=str(occurrence.id),
        action="created",
        payload=_occurrence_payload(occurrence),
    )


def _finalize_updated_occurrence(occurrence, actor, *, previous: dict, changed_fields: list[str]):
    _sync_equipment_operational_status(occurrence.equipment)
    if changed_fields:
        register_audit_event(
            actor_user=actor,
            entity_name="Occurrence",
            entity_id=str(occurrence.id),
            action="updated",
            area=occurrence.area,
            summary=_update_summary(occurrence, changed_fields),
            payload={
                **_occurrence_payload(occurrence),
                "changed_fields": changed_fields,
            },
        )
        enqueue_sync_item(
            entity_name="Occurrence",
            entity_id=str(occurrence.id),
            action="updated",
            payload={"changed_fields": changed_fields},
        )

    if "status" in changed_fields and previous.get("status") != occurrence.status:
        register_audit_event(
            actor_user=actor,
            entity_name="Occurrence",
            entity_id=str(occurrence.id),
            action="status_changed",
            area=occurrence.area,
            summary=f"Status da ocorrencia do equipamento {occurrence.equipment.code} alterado para {_status_label(occurrence.status)}.",
            payload={
                **_occurrence_payload(occurrence),
                "previous_status": previous.get("status"),
            },
        )


def _sync_equipment_operational_status(equipment):
    active_downtime_exists = equipment.occurrences.filter(
        had_downtime=True,
        status__in=ACTIVE_OCCURRENCE_STATUSES,
    ).exists()

    if active_downtime_exists and equipment.status != EquipmentStatus.EXTERNAL_SERVICE:
        target_status = EquipmentStatus.UNDER_MAINTENANCE
    elif not active_downtime_exists and equipment.status == EquipmentStatus.UNDER_MAINTENANCE:
        target_status = EquipmentStatus.ACTIVE
    else:
        target_status = equipment.status

    if target_status != equipment.status:
        equipment.status = target_status
        equipment.save(update_fields=["status", "updated_at"])


def _occurrence_payload(occurrence: Occurrence) -> dict:
    return {
        "occurrence_id": str(occurrence.id),
        "equipment_id": str(occurrence.equipment_id),
        "equipment_code": occurrence.equipment.code,
        "area_id": str(occurrence.area_id),
        "area_code": occurrence.area.code,
        "location_id": str(occurrence.location_id) if occurrence.location_id else "",
        "unidade_id": str(occurrence.unidade_id) if occurrence.unidade_id else "",
        "fabrica_code": occurrence.resolved_fabrica.code if occurrence.resolved_fabrica is not None else "",
        "classification": occurrence.classification,
        "status": occurrence.status,
        "had_downtime": occurrence.had_downtime,
        "downtime_minutes": occurrence.downtime_minutes,
        "occurred_at": occurrence.occurred_at.isoformat(),
        "responsible_collaborator_id": str(occurrence.responsible_collaborator_id or ""),
    }


def _update_summary(occurrence: Occurrence, changed_fields: list[str]) -> str:
    labels = {
        "equipment": "equipamento",
        "location": "local",
        "unidade": "unidade produtiva",
        "responsible_collaborator": "responsavel",
        "classification": "classificacao",
        "description": "descricao",
        "notes": "observacoes",
        "occurred_at": "data/hora",
        "had_downtime": "houve parada",
        "downtime_minutes": "tempo de parada",
    }
    relevant_labels = [labels.get(field, field) for field in changed_fields]
    return f"Ocorrencia do equipamento {occurrence.equipment.code} atualizada ({', '.join(relevant_labels)})."


def _snapshot_occurrence(occurrence: Occurrence) -> dict:
    return {
        "status": occurrence.status,
        "classification": occurrence.classification,
        "location_id": str(occurrence.location_id or ""),
        "unidade_id": str(occurrence.unidade_id or ""),
        "responsible_collaborator_id": str(occurrence.responsible_collaborator_id or ""),
    }


def _status_label(status_value: str) -> str:
    return OccurrenceStatus(status_value).label
