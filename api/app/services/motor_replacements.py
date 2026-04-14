from __future__ import annotations

from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.enums import AreaCode, MotorStatus
from app.core.notification_events import NotificationEventType
from app.core.permissions import PermissionName, ensure_area_access, ensure_permission, ensure_permission_in_area
from app.db.repositories.equipments import EquipmentRepository
from app.db.repositories.motor_replacements import MotorReplacementRepository
from app.db.repositories.motors import MotorRepository
from app.services.audit import AuditService
from app.services.notification import NotificationService
from app.services.trackable_history import TrackableHistoryService


class MotorReplacementService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = MotorReplacementRepository(db)
        self.motor_repository = MotorRepository(db)
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
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Motor replacement not found.")
        ensure_permission_in_area(actor, PermissionName.VIEW_AREA_DATA, replacement.area_id)
        return replacement

    def create_replacement(self, data, actor):
        removed_motor = self.motor_repository.get(data.removed_motor_id)
        installed_motor = self.motor_repository.get(data.installed_motor_id)
        if not removed_motor or not installed_motor:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Motor not found.")
        if removed_motor.equipment_id == installed_motor.equipment_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Removed motor and installed motor must be different.",
            )

        self._ensure_electrical_motor(removed_motor)
        self._ensure_electrical_motor(installed_motor)
        ensure_permission_in_area(actor, PermissionName.CREATE_OCCURRENCES, removed_motor.equipment.area_id)
        ensure_area_access(actor, installed_motor.equipment.area_id)

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
        payload["area_id"] = removed_motor.equipment.area_id
        payload["registered_by_user_id"] = actor.id
        payload["replaced_at"] = replaced_at
        replacement = self.repository.create(payload)

        removed_status = self._removed_motor_status(data.reason)
        installed_location_id = target_equipment.location_id if target_equipment else removed_motor.equipment.location_id
        removed_location_id = target_equipment.location_id if target_equipment else removed_motor.equipment.location_id

        self.history_service.record_event(
            equipment=removed_motor.equipment,
            actor=actor,
            reason=(
                f"Motor removido da tag {data.target_equipment_tag} e substituido por "
                f"{installed_motor.unique_identifier}."
            ),
            status_after=removed_status.value,
            notes=data.notes,
            new_location_id=removed_location_id,
            moved_at=replaced_at,
        )
        self.history_service.record_event(
            equipment=installed_motor.equipment,
            actor=actor,
            reason=(
                f"Motor instalado na tag {data.target_equipment_tag} substituindo "
                f"{removed_motor.unique_identifier}."
            ),
            status_after=MotorStatus.IN_OPERATION.value,
            notes=data.notes,
            new_location_id=installed_location_id,
            moved_at=replaced_at,
        )

        self.audit_service.record(
            actor=actor,
            entity_name="MotorReplacement",
            entity_id=str(replacement.id),
            action="created",
            area_id=replacement.area_id,
            summary=(
                f"Motor {removed_motor.unique_identifier} substituido por "
                f"{installed_motor.unique_identifier}."
            ),
            payload=payload,
        )
        self.notification_service.enqueue(
            event_type=NotificationEventType.MOTOR_REPLACED,
            entity_name="MotorReplacement",
            entity_id=str(replacement.id),
            area_id=replacement.area_id,
            payload={
                "target_equipment_tag": data.target_equipment_tag,
                "removed_motor": removed_motor.unique_identifier,
                "installed_motor": installed_motor.unique_identifier,
                "reason": data.reason,
            },
        )
        self.db.commit()
        return self.repository.get(replacement.id)

    @staticmethod
    def _removed_motor_status(reason: str) -> MotorStatus:
        normalized_reason = reason.lower()
        if "queim" in normalized_reason:
            return MotorStatus.INTERNAL_MAINTENANCE
        return MotorStatus.RESERVE

    @staticmethod
    def _ensure_electrical_motor(motor) -> None:
        if motor.equipment.area.code != AreaCode.ELETRICA:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Motor replacement flow is only available for the electrical area.",
            )

