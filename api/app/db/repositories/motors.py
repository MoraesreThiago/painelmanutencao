from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.core.permissions import apply_area_id_scope
from app.models.equipment import Equipment
from app.models.motor import Motor
from app.models.user import User
from app.db.repositories.base import BaseRepository


class MotorRepository(BaseRepository[Motor]):
    model = Motor

    def get(self, equipment_id) -> Motor | None:
        stmt = (
            select(Motor)
            .where(Motor.equipment_id == equipment_id)
            .options(
                joinedload(Motor.equipment).joinedload(Equipment.area),
                joinedload(Motor.equipment).joinedload(Equipment.location),
            )
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_visible(self, current_user: User) -> list[Motor]:
        stmt = (
            select(Motor)
            .join(Motor.equipment)
            .options(
                joinedload(Motor.equipment).joinedload(Equipment.area),
                joinedload(Motor.equipment).joinedload(Equipment.location),
            )
            .order_by(Equipment.code)
        )
        stmt = apply_area_id_scope(stmt, current_user, Equipment.area_id)
        return self.list(statement=stmt)

