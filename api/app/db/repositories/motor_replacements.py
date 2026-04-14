from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.core.permissions import apply_area_id_scope
from app.models.equipment import Equipment
from app.models.motor import Motor
from app.models.motor_replacement import MotorReplacement
from app.models.user import User
from app.db.repositories.base import BaseRepository


class MotorReplacementRepository(BaseRepository[MotorReplacement]):
    model = MotorReplacement

    def get(self, entity_id) -> MotorReplacement | None:
        stmt = (
            select(MotorReplacement)
            .where(MotorReplacement.id == entity_id)
            .options(
                joinedload(MotorReplacement.removed_motor)
                .joinedload(Motor.equipment)
                .joinedload(Equipment.area),
                joinedload(MotorReplacement.removed_motor)
                .joinedload(Motor.equipment)
                .joinedload(Equipment.location),
                joinedload(MotorReplacement.installed_motor)
                .joinedload(Motor.equipment)
                .joinedload(Equipment.area),
                joinedload(MotorReplacement.installed_motor)
                .joinedload(Motor.equipment)
                .joinedload(Equipment.location),
                joinedload(MotorReplacement.target_equipment).joinedload(Equipment.area),
                joinedload(MotorReplacement.target_equipment).joinedload(Equipment.location),
                joinedload(MotorReplacement.registered_by_user),
            )
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_visible(self, current_user: User) -> list[MotorReplacement]:
        stmt = (
            select(MotorReplacement)
            .options(
                joinedload(MotorReplacement.removed_motor)
                .joinedload(Motor.equipment)
                .joinedload(Equipment.area),
                joinedload(MotorReplacement.removed_motor)
                .joinedload(Motor.equipment)
                .joinedload(Equipment.location),
                joinedload(MotorReplacement.installed_motor)
                .joinedload(Motor.equipment)
                .joinedload(Equipment.area),
                joinedload(MotorReplacement.installed_motor)
                .joinedload(Motor.equipment)
                .joinedload(Equipment.location),
                joinedload(MotorReplacement.target_equipment).joinedload(Equipment.area),
                joinedload(MotorReplacement.target_equipment).joinedload(Equipment.location),
                joinedload(MotorReplacement.registered_by_user),
            )
            .order_by(MotorReplacement.replaced_at.desc())
        )
        stmt = apply_area_id_scope(stmt, current_user, MotorReplacement.area_id)
        return self.list(statement=stmt)

