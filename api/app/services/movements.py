from __future__ import annotations

from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.enums import InstrumentStatus, MotorStatus
from app.core.notification_events import NotificationEventType
from app.core.permissions import PermissionName, ensure_area_access, ensure_permission, ensure_permission_in_area
from app.models.user import User
from app.db.repositories.equipments import EquipmentRepository
from app.db.repositories.locations import LocationRepository
from app.db.repositories.movements import MovementRepository
from app.services.audit import AuditService
from app.services.equipments import EquipmentService
from app.services.notification import NotificationService


class MovementService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = MovementRepository(db)
        self.equipment_repository = EquipmentRepository(db)
        self.location_repository = LocationRepository(db)
        self.audit_service = AuditService(db)
        self.notification_service = NotificationService(db)
        self.equipment_service = EquipmentService(db)

    def list_movements(self, current_user: User):
        ensure_permission(current_user, PermissionName.VIEW_AREA_DATA)
        return self.repository.list_visible(current_user)

    def get_movement(self, movement_id, actor: User):
        movement = self.repository.get(movement_id)
        if not movement:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movement not found.")
        ensure_permission_in_area(actor, PermissionName.VIEW_AREA_DATA, movement.equipment.area_id)
        return movement

    def create_movement(self, data, actor: User):
        equipment = self.equipment_repository.get(data.equipment_id)
        if not equipment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipment not found.")
        ensure_permission_in_area(actor, PermissionName.CREATE_OCCURRENCES, equipment.area_id)

        if data.new_location_id:
            new_location = self.location_repository.get(data.new_location_id)
            if not new_location:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Destination location not found.",
                )
            ensure_area_access(actor, new_location.area_id)

        payload = data.model_dump()
        payload["previous_location_id"] = equipment.location_id
        payload["moved_by_user_id"] = actor.id
        payload["moved_at"] = data.moved_at or datetime.now(UTC)

        movement = self.repository.create(payload)
        equipment.location_id = data.new_location_id
        if data.status_after:
            equipment.status = self.equipment_service.map_trackable_status_to_equipment_status(
                data.status_after,
            )
            if equipment.motor:
                try:
                    equipment.motor.current_status = MotorStatus(data.status_after)
                except ValueError:
                    pass
            if equipment.instrument:
                try:
                    equipment.instrument.current_status = InstrumentStatus(data.status_after)
                except ValueError:
                    pass

        self.audit_service.record(
            actor=actor,
            entity_name="Movement",
            entity_id=str(movement.id),
            action="created",
            area_id=equipment.area_id,
            summary=f"Movement recorded for equipment {equipment.code}.",
            payload=payload,
        )
        self.notification_service.enqueue(
            event_type=NotificationEventType.MOVEMENT_RECORDED,
            entity_name="Equipment",
            entity_id=str(equipment.id),
            area_id=equipment.area_id,
            payload={
                "equipment_code": equipment.code,
                "reason": data.reason,
                "status_after": data.status_after,
            },
        )
        self.db.commit()
        return self.repository.get(movement.id)

    def delete_movement(self, movement_id, actor: User):
        movement = self.get_movement(movement_id, actor)
        ensure_permission_in_area(actor, PermissionName.DELETE_OCCURRENCES, movement.equipment.area_id)
        self.audit_service.record(
            actor=actor,
            entity_name="Movement",
            entity_id=str(movement.id),
            action="deleted",
            area_id=movement.equipment.area_id,
            summary="Movement deleted.",
        )
        self.repository.delete(movement)
        self.db.commit()

