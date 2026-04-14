from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.enums import EquipmentStatus, ExternalServiceStatus, MotorStatus
from app.core.notification_events import NotificationEventType
from app.core.permissions import PermissionName, ensure_permission, ensure_permission_in_area
from app.models.movement import Movement
from app.models.user import User
from app.db.repositories.external_service_orders import ExternalServiceOrderRepository
from app.db.repositories.motors import MotorRepository
from app.services.audit import AuditService
from app.services.notification import NotificationService


class ExternalServiceOrderService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = ExternalServiceOrderRepository(db)
        self.motor_repository = MotorRepository(db)
        self.audit_service = AuditService(db)
        self.notification_service = NotificationService(db)

    def list_orders(self, current_user: User):
        ensure_permission(current_user, PermissionName.MANAGE_EXTERNAL_SERVICE)
        return self.repository.list_visible(current_user)

    def get_order(self, order_id, actor: User):
        order = self.repository.get(order_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="External service order not found.",
            )
        ensure_permission_in_area(actor, PermissionName.MANAGE_EXTERNAL_SERVICE, order.motor.equipment.area_id)
        return order

    def create_order(self, data, actor: User):
        motor = self.motor_repository.get(data.motor_id)
        if not motor:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Motor not found.")
        ensure_permission_in_area(actor, PermissionName.MANAGE_EXTERNAL_SERVICE, motor.equipment.area_id)

        payload = data.model_dump()
        payload["registered_by_user_id"] = actor.id
        order = self.repository.create(payload)

        motor.current_status = MotorStatus.EXTERNAL_SERVICE
        motor.equipment.status = EquipmentStatus.EXTERNAL_SERVICE

        movement = Movement(
            equipment_id=motor.equipment_id,
            previous_location_id=motor.equipment.location_id,
            new_location_id=None,
            moved_by_user_id=actor.id,
            reason=f"External service exit: {data.reason}",
            status_after=MotorStatus.EXTERNAL_SERVICE.value,
            notes=data.notes,
        )
        motor.equipment.location_id = None
        self.db.add(movement)

        self.audit_service.record(
            actor=actor,
            entity_name="ExternalServiceOrder",
            entity_id=str(order.id),
            action="created",
            area_id=motor.equipment.area_id,
            summary=f"External service order {order.work_order_number} created.",
            payload=payload,
        )
        self.notification_service.enqueue(
            event_type=NotificationEventType.MOTOR_SENT_EXTERNAL_SERVICE,
            entity_name="Motor",
            entity_id=str(motor.equipment_id),
            area_id=motor.equipment.area_id,
            payload={
                "work_order_number": data.work_order_number,
                "vendor_name": data.vendor_name,
                "expected_return_at": data.expected_return_at,
            },
        )
        self.db.commit()
        return self.repository.get(order.id)

    def update_order(self, order_id, data, actor: User):
        order = self.get_order(order_id, actor)
        payload = data.model_dump(exclude_unset=True)
        updated = self.repository.update(order, payload)

        if updated.service_status == ExternalServiceStatus.RETURNED and updated.actual_return_at:
            updated.motor.current_status = MotorStatus.AWAITING_INSTALLATION
            updated.motor.equipment.status = EquipmentStatus.ACTIVE
            self.notification_service.enqueue(
                event_type=NotificationEventType.MOTOR_RETURNED_EXTERNAL_SERVICE,
                entity_name="Motor",
                entity_id=str(updated.motor.equipment_id),
                area_id=updated.motor.equipment.area_id,
                payload={
                    "work_order_number": updated.work_order_number,
                    "actual_return_at": updated.actual_return_at,
                },
            )

        self.audit_service.record(
            actor=actor,
            entity_name="ExternalServiceOrder",
            entity_id=str(updated.id),
            action="updated",
            area_id=updated.motor.equipment.area_id,
            summary=f"External service order {updated.work_order_number} updated.",
            payload=payload,
        )
        self.db.commit()
        return self.repository.get(updated.id)

    def delete_order(self, order_id, actor: User):
        order = self.get_order(order_id, actor)
        self.audit_service.record(
            actor=actor,
            entity_name="ExternalServiceOrder",
            entity_id=str(order.id),
            action="deleted",
            area_id=order.motor.equipment.area_id,
            summary=f"External service order {order.work_order_number} deleted.",
        )
        self.repository.delete(order)
        self.db.commit()

