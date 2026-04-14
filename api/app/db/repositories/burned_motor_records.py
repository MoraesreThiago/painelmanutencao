from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.core.permissions import apply_area_id_scope
from app.models.burned_motor_record import BurnedMotorRecord
from app.models.equipment import Equipment
from app.models.motor import Motor
from app.models.motor_replacement import MotorReplacement
from app.models.user import User
from app.db.repositories.base import BaseRepository


class BurnedMotorRecordRepository(BaseRepository[BurnedMotorRecord]):
    model = BurnedMotorRecord

    def get(self, entity_id) -> BurnedMotorRecord | None:
        stmt = (
            select(BurnedMotorRecord)
            .where(BurnedMotorRecord.id == entity_id)
            .options(
                joinedload(BurnedMotorRecord.motor).joinedload(Motor.equipment).joinedload(Equipment.area),
                joinedload(BurnedMotorRecord.motor).joinedload(Motor.equipment).joinedload(Equipment.location),
                joinedload(BurnedMotorRecord.motor_replacement)
                .joinedload(MotorReplacement.removed_motor)
                .joinedload(Motor.equipment),
                joinedload(BurnedMotorRecord.motor_replacement)
                .joinedload(MotorReplacement.installed_motor)
                .joinedload(Motor.equipment),
                joinedload(BurnedMotorRecord.recorded_by_user),
            )
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_visible(self, current_user: User) -> list[BurnedMotorRecord]:
        stmt = (
            select(BurnedMotorRecord)
            .options(
                joinedload(BurnedMotorRecord.motor).joinedload(Motor.equipment).joinedload(Equipment.area),
                joinedload(BurnedMotorRecord.motor).joinedload(Motor.equipment).joinedload(Equipment.location),
                joinedload(BurnedMotorRecord.motor_replacement)
                .joinedload(MotorReplacement.removed_motor)
                .joinedload(Motor.equipment),
                joinedload(BurnedMotorRecord.motor_replacement)
                .joinedload(MotorReplacement.installed_motor)
                .joinedload(Motor.equipment),
                joinedload(BurnedMotorRecord.recorded_by_user),
            )
            .order_by(BurnedMotorRecord.recorded_at.desc())
        )
        stmt = apply_area_id_scope(stmt, current_user, BurnedMotorRecord.area_id)
        return self.list(statement=stmt)

