from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.enums import EquipmentType
from app.core.notification_events import NotificationEventType
from app.core.permissions import PermissionName, ensure_permission, ensure_permission_in_area
from app.models.motor import Motor
from app.models.user import User
from app.db.repositories.motors import MotorRepository
from app.services.audit import AuditService
from app.services.equipments import EquipmentService
from app.services.notification import NotificationService


class MotorService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = MotorRepository(db)
        self.equipment_service = EquipmentService(db)
        self.audit_service = AuditService(db)
        self.notification_service = NotificationService(db)

    def list_motors(self, current_user: User):
        ensure_permission(current_user, PermissionName.VIEW_AREA_DATA)
        return self.repository.list_visible(current_user)

    def get_motor(self, motor_id, actor: User):
        motor = self.repository.get(motor_id)
        if not motor:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Motor not found.")
        ensure_permission_in_area(actor, PermissionName.VIEW_AREA_DATA, motor.equipment.area_id)
        return motor

    def create_motor(self, data, actor: User):
        ensure_permission_in_area(actor, PermissionName.MANAGE_AREA_DATA, data.area_id)
        equipment = self.equipment_service.create_equipment(
            data,
            actor,
            equipment_type=EquipmentType.MOTOR,
            commit=False,
        )
        motor = Motor(
            equipment_id=equipment.id,
            unique_identifier=data.unique_identifier,
            current_status=data.current_status,
            last_internal_service_at=data.last_internal_service_at,
        )
        equipment.status = self.equipment_service.map_trackable_status_to_equipment_status(
            data.current_status.value,
        )
        self.db.add(motor)
        self.audit_service.record(
            actor=actor,
            entity_name="Motor",
            entity_id=str(equipment.id),
            action="created",
            area_id=equipment.area_id,
            summary=f"Motor {data.unique_identifier} created.",
            payload=data.model_dump(),
        )
        self.notification_service.enqueue(
            event_type=NotificationEventType.MOTOR_CREATED,
            entity_name="Motor",
            entity_id=str(equipment.id),
            area_id=equipment.area_id,
            payload=data.model_dump(),
        )
        self.db.commit()
        return self.repository.get(equipment.id)

    def update_motor(self, motor_id, data, actor: User):
        motor = self.get_motor(motor_id, actor)
        ensure_permission_in_area(actor, PermissionName.MANAGE_AREA_DATA, motor.equipment.area_id)
        payload = data.model_dump(exclude_unset=True)

        equipment_payload = {
            key: value
            for key, value in payload.items()
            if key
            in {
                "code",
                "tag",
                "description",
                "sector",
                "manufacturer",
                "model",
                "serial_number",
                "notes",
                "status",
                "area_id",
                "location_id",
            }
        }
        motor_payload = {
            key: value
            for key, value in payload.items()
            if key in {"unique_identifier", "current_status", "last_internal_service_at"}
        }

        if equipment_payload:
            self.equipment_service.repository.update(motor.equipment, equipment_payload)
        if motor_payload:
            self.repository.update(motor, motor_payload)
        if "current_status" in motor_payload:
            motor.equipment.status = self.equipment_service.map_trackable_status_to_equipment_status(
                motor_payload["current_status"].value,
            )

        self.audit_service.record(
            actor=actor,
            entity_name="Motor",
            entity_id=str(motor.equipment_id),
            action="updated",
            area_id=motor.equipment.area_id,
            summary=f"Motor {motor.unique_identifier} updated.",
            payload=payload,
        )
        self.db.commit()
        return self.repository.get(motor.equipment_id)

    def delete_motor(self, motor_id, actor: User):
        motor = self.get_motor(motor_id, actor)
        ensure_permission_in_area(actor, PermissionName.DELETE_AREA_DATA, motor.equipment.area_id)
        self.audit_service.record(
            actor=actor,
            entity_name="Motor",
            entity_id=str(motor.equipment_id),
            action="deleted",
            area_id=motor.equipment.area_id,
            summary=f"Motor {motor.unique_identifier} deleted.",
        )
        self.equipment_service.repository.delete(motor.equipment)
        self.db.commit()

