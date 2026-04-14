from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.enums import EquipmentType
from app.core.notification_events import NotificationEventType
from app.core.permissions import PermissionName, ensure_permission, ensure_permission_in_area
from app.models.instrument import Instrument
from app.models.user import User
from app.db.repositories.instruments import InstrumentRepository
from app.services.audit import AuditService
from app.services.equipments import EquipmentService
from app.services.notification import NotificationService


class InstrumentService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = InstrumentRepository(db)
        self.equipment_service = EquipmentService(db)
        self.audit_service = AuditService(db)
        self.notification_service = NotificationService(db)

    def list_instruments(self, current_user: User):
        ensure_permission(current_user, PermissionName.VIEW_AREA_DATA)
        return self.repository.list_visible(current_user)

    def get_instrument(self, instrument_id, actor: User):
        instrument = self.repository.get(instrument_id)
        if not instrument:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Instrument not found.",
            )
        ensure_permission_in_area(actor, PermissionName.VIEW_AREA_DATA, instrument.equipment.area_id)
        return instrument

    def create_instrument(self, data, actor: User):
        ensure_permission_in_area(actor, PermissionName.MANAGE_AREA_DATA, data.area_id)
        equipment = self.equipment_service.create_equipment(
            data,
            actor,
            equipment_type=EquipmentType.INSTRUMENT,
            commit=False,
        )
        instrument = Instrument(
            equipment_id=equipment.id,
            unique_identifier=data.unique_identifier,
            instrument_type=data.instrument_type,
            current_status=data.current_status,
            calibration_due_date=data.calibration_due_date,
        )
        equipment.status = self.equipment_service.map_trackable_status_to_equipment_status(
            data.current_status.value,
        )
        self.db.add(instrument)
        self.audit_service.record(
            actor=actor,
            entity_name="Instrument",
            entity_id=str(equipment.id),
            action="created",
            area_id=equipment.area_id,
            summary=f"Instrument {data.unique_identifier} created.",
            payload=data.model_dump(),
        )
        self.notification_service.enqueue(
            event_type=NotificationEventType.INSTRUMENT_CREATED,
            entity_name="Instrument",
            entity_id=str(equipment.id),
            area_id=equipment.area_id,
            payload=data.model_dump(),
        )
        self.db.commit()
        return self.repository.get(equipment.id)

    def update_instrument(self, instrument_id, data, actor: User):
        instrument = self.get_instrument(instrument_id, actor)
        ensure_permission_in_area(actor, PermissionName.MANAGE_AREA_DATA, instrument.equipment.area_id)
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
        instrument_payload = {
            key: value
            for key, value in payload.items()
            if key in {"unique_identifier", "instrument_type", "current_status", "calibration_due_date"}
        }

        if equipment_payload:
            self.equipment_service.repository.update(instrument.equipment, equipment_payload)
        if instrument_payload:
            self.repository.update(instrument, instrument_payload)
        if "current_status" in instrument_payload:
            instrument.equipment.status = self.equipment_service.map_trackable_status_to_equipment_status(
                instrument_payload["current_status"].value,
            )

        self.audit_service.record(
            actor=actor,
            entity_name="Instrument",
            entity_id=str(instrument.equipment_id),
            action="updated",
            area_id=instrument.equipment.area_id,
            summary=f"Instrument {instrument.unique_identifier} updated.",
            payload=payload,
        )
        self.db.commit()
        return self.repository.get(instrument.equipment_id)

    def delete_instrument(self, instrument_id, actor: User):
        instrument = self.get_instrument(instrument_id, actor)
        ensure_permission_in_area(actor, PermissionName.DELETE_AREA_DATA, instrument.equipment.area_id)
        self.audit_service.record(
            actor=actor,
            entity_name="Instrument",
            entity_id=str(instrument.equipment_id),
            action="deleted",
            area_id=instrument.equipment.area_id,
            summary=f"Instrument {instrument.unique_identifier} deleted.",
        )
        self.equipment_service.repository.delete(instrument.equipment)
        self.db.commit()

