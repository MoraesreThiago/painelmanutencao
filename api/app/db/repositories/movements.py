from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.core.permissions import apply_area_id_scope
from app.models.equipment import Equipment
from app.models.movement import Movement
from app.models.user import User
from app.db.repositories.base import BaseRepository


class MovementRepository(BaseRepository[Movement]):
    model = Movement

    def get(self, entity_id) -> Movement | None:
        stmt = (
            select(Movement)
            .where(Movement.id == entity_id)
            .options(
                joinedload(Movement.equipment).joinedload(Equipment.area),
                joinedload(Movement.equipment).joinedload(Equipment.location),
                joinedload(Movement.previous_location),
                joinedload(Movement.new_location),
                joinedload(Movement.moved_by_user),
            )
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_visible(self, current_user: User) -> list[Movement]:
        stmt = (
            select(Movement)
            .join(Movement.equipment)
            .options(
                joinedload(Movement.equipment).joinedload(Equipment.area),
                joinedload(Movement.equipment).joinedload(Equipment.location),
                joinedload(Movement.previous_location),
                joinedload(Movement.new_location),
                joinedload(Movement.moved_by_user),
            )
            .order_by(Movement.moved_at.desc())
        )
        stmt = apply_area_id_scope(stmt, current_user, Equipment.area_id)
        return self.list(statement=stmt)

