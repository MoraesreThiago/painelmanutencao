from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from app.core.enums import InstrumentStatus, MotorStatus
from app.models.equipment import Equipment
from app.models.movement import Movement
from app.models.user import User
from app.services.equipments import EquipmentService


class _KeepLocation:
    pass


KEEP_LOCATION = _KeepLocation()


class TrackableHistoryService:
    def __init__(self, db):
        self.db = db
        self.equipment_service = EquipmentService(db)

    def record_event(
        self,
        *,
        equipment: Equipment,
        actor: User,
        reason: str,
        status_after: str | None = None,
        notes: str | None = None,
        new_location_id: UUID | None | _KeepLocation = KEEP_LOCATION,
        moved_at: datetime | None = None,
    ) -> Movement:
        previous_location_id = equipment.location_id
        next_location_id = equipment.location_id if new_location_id is KEEP_LOCATION else new_location_id

        movement = Movement(
            equipment_id=equipment.id,
            previous_location_id=previous_location_id,
            new_location_id=next_location_id,
            moved_by_user_id=actor.id,
            moved_at=moved_at or datetime.now(UTC),
            reason=reason,
            status_after=status_after,
            notes=notes,
        )
        self.db.add(movement)

        if new_location_id is not KEEP_LOCATION:
            equipment.location_id = next_location_id

        if status_after:
            equipment.status = self.equipment_service.map_trackable_status_to_equipment_status(status_after)
            if equipment.motor:
                try:
                    equipment.motor.current_status = MotorStatus(status_after)
                except ValueError:
                    pass
            if equipment.instrument:
                try:
                    equipment.instrument.current_status = InstrumentStatus(status_after)
                except ValueError:
                    pass

        self.db.add(equipment)
        self.db.flush()
        return movement

