from __future__ import annotations

from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.enums import AreaCode, InstrumentStatus
from app.core.notification_events import NotificationEventType
from app.core.permissions import PermissionName, ensure_area_access, ensure_permission, ensure_permission_in_area
from app.db.repositories.equipments import EquipmentRepository
from app.db.repositories.instrument_replacements import InstrumentReplacementRepository
from app.db.repositories.instruments import InstrumentRepository
from app.services.audit import AuditService
from app.services.notification import NotificationService
from app.services.trackable_history import TrackableHistoryService


class InstrumentReplacementService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = InstrumentReplacementRepository(db)
        self.instrument_repository = InstrumentRepository(db)
        self.equipment_repository = EquipmentRepository(db)
        self.audit_service = AuditService(db)
        self.notification_service = NotificationService(db)
        self.history_service = TrackableHistoryService(db)

    def list_replacements(self, current_user):
        ensure_permission(current_user, PermissionName.VIEW_AREA_DATA)
        return self.repository.list_visible(current_user)

    def get_replacement(self, replacement_id, actor):
        replacement = self.repository.get(replacement_id)
        if not replacement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Instrument replacement not found.",
            )
        ensure_permission_in_area(actor, PermissionName.VIEW_AREA_DATA, replacement.area_id)
        return replacement

    def create_replacement(self, data, actor):
        removed_instrument = self.instrument_repository.get(data.removed_instrument_id)
        installed_instrument = self.instrument_repository.get(data.installed_instrument_id)
        if not removed_instrument or not installed_instrument:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Instrument not found.")
        if removed_instrument.equipment_id == installed_instrument.equipment_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Removed instrument and installed instrument must be different.",
            )

        self._ensure_instrumentation_item(removed_instrument)
        self._ensure_instrumentation_item(installed_instrument)
        ensure_permission_in_area(
            actor,
            PermissionName.CREATE_OCCURRENCES,
            removed_instrument.equipment.area_id,
        )
        ensure_area_access(actor, installed_instrument.equipment.area_id)

        target_equipment = None
        if data.target_equipment_id:
            target_equipment = self.equipment_repository.get(data.target_equipment_id)
            if not target_equipment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Target equipment not found.",
                )
            ensure_area_access(actor, target_equipment.area_id)

        replaced_at = data.replaced_at or datetime.now(UTC)
        payload = data.model_dump()
        payload["area_id"] = removed_instrument.equipment.area_id
        payload["registered_by_user_id"] = actor.id
        payload["replaced_at"] = replaced_at
        replacement = self.repository.create(payload)

        target_location_id = (
            target_equipment.location_id if target_equipment else removed_instrument.equipment.location_id
        )

        self.history_service.record_event(
            equipment=removed_instrument.equipment,
            actor=actor,
            reason=(
                f"Instrumento removido da tag {data.target_equipment_tag} e substituido por "
                f"{installed_instrument.unique_identifier}."
            ),
            status_after=InstrumentStatus.IN_STOCK.value,
            notes=data.notes,
            new_location_id=target_location_id,
            moved_at=replaced_at,
        )
        self.history_service.record_event(
            equipment=installed_instrument.equipment,
            actor=actor,
            reason=(
                f"Instrumento instalado na tag {data.target_equipment_tag} substituindo "
                f"{removed_instrument.unique_identifier}."
            ),
            status_after=InstrumentStatus.INSTALLED.value,
            notes=data.notes,
            new_location_id=target_location_id,
            moved_at=replaced_at,
        )

        self.audit_service.record(
            actor=actor,
            entity_name="InstrumentReplacement",
            entity_id=str(replacement.id),
            action="created",
            area_id=replacement.area_id,
            summary=(
                f"Instrumento {removed_instrument.unique_identifier} substituido por "
                f"{installed_instrument.unique_identifier}."
            ),
            payload=payload,
        )
        self.notification_service.enqueue(
            event_type=NotificationEventType.INSTRUMENT_REPLACED,
            entity_name="InstrumentReplacement",
            entity_id=str(replacement.id),
            area_id=replacement.area_id,
            payload={
                "target_equipment_tag": data.target_equipment_tag,
                "removed_instrument": removed_instrument.unique_identifier,
                "installed_instrument": installed_instrument.unique_identifier,
                "reason": data.reason,
            },
        )
        self.db.commit()
        return self.repository.get(replacement.id)

    @staticmethod
    def _ensure_instrumentation_item(instrument) -> None:
        if instrument.equipment.area.code != AreaCode.INSTRUMENTACAO:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Instrument replacement flow is only available for the instrumentation area.",
            )

