from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.core.permissions import apply_area_scope
from app.models.equipment import Equipment
from app.models.user import User
from app.db.repositories.base import BaseRepository


class EquipmentRepository(BaseRepository[Equipment]):
    model = Equipment

    def get(self, entity_id) -> Equipment | None:
        stmt = (
            select(Equipment)
            .where(Equipment.id == entity_id)
            .options(
                joinedload(Equipment.area),
                joinedload(Equipment.location),
                joinedload(Equipment.motor),
                joinedload(Equipment.instrument),
            )
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_visible(self, current_user: User) -> list[Equipment]:
        stmt = (
            apply_area_scope(select(Equipment), current_user, Equipment)
            .options(joinedload(Equipment.area), joinedload(Equipment.location))
            .order_by(Equipment.code)
        )
        return self.list(statement=stmt)

