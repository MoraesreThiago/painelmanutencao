from __future__ import annotations

from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.enums import EquipmentStatus, EquipmentType
from app.core.permissions import PermissionName, ensure_permission, ensure_permission_in_area
from app.models.user import User
from app.db.repositories.equipments import EquipmentRepository
from app.services.audit import AuditService


class EquipmentService:
    EQUIPMENT_FIELDS = {
        "code",
        "tag",
        "description",
        "sector",
        "manufacturer",
        "model",
        "serial_number",
        "notes",
        "status",
        "registered_at",
        "area_id",
        "location_id",
    }

    def __init__(self, db: Session):
        self.db = db
        self.repository = EquipmentRepository(db)
        self.audit_service = AuditService(db)

    def list_equipments(self, current_user: User):
        ensure_permission(current_user, PermissionName.VIEW_AREA_DATA)
        return self.repository.list_visible(current_user)

    def get_equipment(self, equipment_id, actor: User):
        equipment = self.repository.get(equipment_id)
        if not equipment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipment not found.")
        ensure_permission_in_area(actor, PermissionName.VIEW_AREA_DATA, equipment.area_id)
        return equipment

    def create_equipment(
        self,
        data,
        actor: User,
        *,
        equipment_type: EquipmentType = EquipmentType.GENERIC,
        commit: bool = True,
    ):
        ensure_permission_in_area(actor, PermissionName.MANAGE_AREA_DATA, data.area_id)
        payload = {
            key: value
            for key, value in data.model_dump().items()
            if key in self.EQUIPMENT_FIELDS
        }
        payload["type"] = equipment_type
        payload["registered_at"] = data.registered_at or datetime.now(UTC)
        equipment = self.repository.create(payload)
        self.audit_service.record(
            actor=actor,
            entity_name="Equipment",
            entity_id=str(equipment.id),
            action="created",
            area_id=equipment.area_id,
            summary=f"Equipment {equipment.code} created.",
            payload=payload,
        )
        if commit:
            self.db.commit()
            return self.repository.get(equipment.id)
        return equipment

    def update_equipment(self, equipment_id, data, actor: User):
        equipment = self.get_equipment(equipment_id, actor)
        payload = data.model_dump(exclude_unset=True)
        ensure_permission_in_area(
            actor,
            PermissionName.MANAGE_AREA_DATA,
            payload.get("area_id", equipment.area_id),
        )
        updated = self.repository.update(equipment, payload)
        self.audit_service.record(
            actor=actor,
            entity_name="Equipment",
            entity_id=str(updated.id),
            action="updated",
            area_id=updated.area_id,
            summary=f"Equipment {updated.code} updated.",
            payload=payload,
        )
        self.db.commit()
        return self.repository.get(updated.id)

    def delete_equipment(self, equipment_id, actor: User):
        equipment = self.get_equipment(equipment_id, actor)
        ensure_permission_in_area(actor, PermissionName.DELETE_AREA_DATA, equipment.area_id)
        self.audit_service.record(
            actor=actor,
            entity_name="Equipment",
            entity_id=str(equipment.id),
            action="deleted",
            area_id=equipment.area_id,
            summary=f"Equipment {equipment.code} deleted.",
        )
        self.repository.delete(equipment)
        self.db.commit()

    @staticmethod
    def map_trackable_status_to_equipment_status(status_value: str | None) -> EquipmentStatus:
        if status_value == "EXTERNAL_SERVICE":
            return EquipmentStatus.EXTERNAL_SERVICE
        if status_value in {"INTERNAL_MAINTENANCE", "IN_MAINTENANCE", "IN_CALIBRATION"}:
            return EquipmentStatus.UNDER_MAINTENANCE
        if status_value == "INACTIVE":
            return EquipmentStatus.INACTIVE
        return EquipmentStatus.ACTIVE

