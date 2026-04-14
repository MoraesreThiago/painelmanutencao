from __future__ import annotations

from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.enums import AreaCode, BurnedMotorStatus, MotorStatus
from app.core.notification_events import NotificationEventType
from app.core.permissions import PermissionName, ensure_area_access, ensure_permission, ensure_permission_in_area
from app.db.repositories.burned_motor_records import BurnedMotorRecordRepository
from app.db.repositories.motor_replacements import MotorReplacementRepository
from app.db.repositories.motors import MotorRepository
from app.services.audit import AuditService
from app.services.notification import NotificationService
from app.services.trackable_history import TrackableHistoryService


class BurnedMotorRecordService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = BurnedMotorRecordRepository(db)
        self.motor_repository = MotorRepository(db)
        self.motor_replacement_repository = MotorReplacementRepository(db)
        self.audit_service = AuditService(db)
        self.notification_service = NotificationService(db)
        self.history_service = TrackableHistoryService(db)

    def list_records(self, current_user):
        ensure_permission(current_user, PermissionName.VIEW_AREA_DATA)
        return self.repository.list_visible(current_user)

    def get_record(self, record_id, actor):
        record = self.repository.get(record_id)
        if not record:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Burned motor record not found.")
        ensure_permission_in_area(actor, PermissionName.VIEW_AREA_DATA, record.area_id)
        return record

    def create_record(self, data, actor):
        motor = self.motor_repository.get(data.motor_id)
        if not motor:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Motor not found.")
        self._ensure_electrical_motor(motor)
        ensure_permission_in_area(actor, PermissionName.CREATE_OCCURRENCES, motor.equipment.area_id)

        if data.motor_replacement_id:
            replacement = self.motor_replacement_repository.get(data.motor_replacement_id)
            if not replacement:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Motor replacement not found.",
                )
            ensure_area_access(actor, replacement.area_id)

        payload = data.model_dump()
        payload["area_id"] = motor.equipment.area_id
        payload["recorded_by_user_id"] = actor.id
        payload["recorded_at"] = data.recorded_at or datetime.now(UTC)
        record = self.repository.create(payload)

        self.history_service.record_event(
            equipment=motor.equipment,
            actor=actor,
            reason=f"Motor classificado como queimado na tag {data.source_equipment_tag}.",
            status_after=self._map_motor_status(record.status).value,
            notes=data.notes or data.diagnosis,
            moved_at=payload["recorded_at"],
        )

        self.audit_service.record(
            actor=actor,
            entity_name="BurnedMotorRecord",
            entity_id=str(record.id),
            action="created",
            area_id=record.area_id,
            summary=f"Motor {motor.unique_identifier} registrado como queimado.",
            payload=payload,
        )
        self.notification_service.enqueue(
            event_type=NotificationEventType.MOTOR_BURNED_RECORDED,
            entity_name="BurnedMotorRecord",
            entity_id=str(record.id),
            area_id=record.area_id,
            payload={
                "motor": motor.unique_identifier,
                "source_equipment_tag": data.source_equipment_tag,
                "status": record.status.value,
            },
        )
        self.db.commit()
        return self.repository.get(record.id)

    def update_record(self, record_id, data, actor):
        record = self.get_record(record_id, actor)
        ensure_permission_in_area(actor, PermissionName.EDIT_OCCURRENCES, record.area_id)
        payload = data.model_dump(exclude_unset=True)
        if "recorded_at" in payload and payload["recorded_at"] is None:
            payload.pop("recorded_at")
        updated = self.repository.update(record, payload)

        mapped_status = self._map_motor_status(updated.status)
        updated.motor.current_status = mapped_status
        updated.motor.equipment.status = self.history_service.equipment_service.map_trackable_status_to_equipment_status(
            mapped_status.value,
        )

        self.audit_service.record(
            actor=actor,
            entity_name="BurnedMotorRecord",
            entity_id=str(updated.id),
            action="updated",
            area_id=updated.area_id,
            summary=f"Registro de motor queimado {updated.motor.unique_identifier} atualizado.",
            payload=payload,
        )
        self.notification_service.enqueue(
            event_type=NotificationEventType.MOTOR_BURNED_STATUS_CHANGED,
            entity_name="BurnedMotorRecord",
            entity_id=str(updated.id),
            area_id=updated.area_id,
            payload={"status": updated.status.value},
        )
        self.db.commit()
        return self.repository.get(updated.id)

    @staticmethod
    def _map_motor_status(record_status: BurnedMotorStatus) -> MotorStatus:
        if record_status == BurnedMotorStatus.REPAIRED:
            return MotorStatus.RESERVE
        if record_status == BurnedMotorStatus.DISCARDED:
            return MotorStatus.INACTIVE
        return MotorStatus.INTERNAL_MAINTENANCE

    @staticmethod
    def _ensure_electrical_motor(motor) -> None:
        if motor.equipment.area.code != AreaCode.ELETRICA:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Burned motor flow is only available for the electrical area.",
            )

