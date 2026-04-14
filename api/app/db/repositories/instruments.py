from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.core.permissions import apply_area_id_scope
from app.models.equipment import Equipment
from app.models.instrument import Instrument
from app.models.user import User
from app.db.repositories.base import BaseRepository


class InstrumentRepository(BaseRepository[Instrument]):
    model = Instrument

    def get(self, equipment_id) -> Instrument | None:
        stmt = (
            select(Instrument)
            .where(Instrument.equipment_id == equipment_id)
            .options(
                joinedload(Instrument.equipment).joinedload(Equipment.area),
                joinedload(Instrument.equipment).joinedload(Equipment.location),
            )
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_visible(self, current_user: User) -> list[Instrument]:
        stmt = (
            select(Instrument)
            .join(Instrument.equipment)
            .options(
                joinedload(Instrument.equipment).joinedload(Equipment.area),
                joinedload(Instrument.equipment).joinedload(Equipment.location),
            )
            .order_by(Equipment.code)
        )
        stmt = apply_area_id_scope(stmt, current_user, Equipment.area_id)
        return self.list(statement=stmt)

