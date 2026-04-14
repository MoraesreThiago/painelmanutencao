from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.core.permissions import apply_area_id_scope
from app.models.equipment import Equipment
from app.models.instrument import Instrument
from app.models.instrument_replacement import InstrumentReplacement
from app.models.user import User
from app.db.repositories.base import BaseRepository


class InstrumentReplacementRepository(BaseRepository[InstrumentReplacement]):
    model = InstrumentReplacement

    def get(self, entity_id) -> InstrumentReplacement | None:
        stmt = (
            select(InstrumentReplacement)
            .where(InstrumentReplacement.id == entity_id)
            .options(
                joinedload(InstrumentReplacement.removed_instrument)
                .joinedload(Instrument.equipment)
                .joinedload(Equipment.area),
                joinedload(InstrumentReplacement.removed_instrument)
                .joinedload(Instrument.equipment)
                .joinedload(Equipment.location),
                joinedload(InstrumentReplacement.installed_instrument)
                .joinedload(Instrument.equipment)
                .joinedload(Equipment.area),
                joinedload(InstrumentReplacement.installed_instrument)
                .joinedload(Instrument.equipment)
                .joinedload(Equipment.location),
                joinedload(InstrumentReplacement.target_equipment).joinedload(Equipment.area),
                joinedload(InstrumentReplacement.target_equipment).joinedload(Equipment.location),
                joinedload(InstrumentReplacement.registered_by_user),
            )
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_visible(self, current_user: User) -> list[InstrumentReplacement]:
        stmt = (
            select(InstrumentReplacement)
            .options(
                joinedload(InstrumentReplacement.removed_instrument)
                .joinedload(Instrument.equipment)
                .joinedload(Equipment.area),
                joinedload(InstrumentReplacement.removed_instrument)
                .joinedload(Instrument.equipment)
                .joinedload(Equipment.location),
                joinedload(InstrumentReplacement.installed_instrument)
                .joinedload(Instrument.equipment)
                .joinedload(Equipment.area),
                joinedload(InstrumentReplacement.installed_instrument)
                .joinedload(Instrument.equipment)
                .joinedload(Equipment.location),
                joinedload(InstrumentReplacement.target_equipment).joinedload(Equipment.area),
                joinedload(InstrumentReplacement.target_equipment).joinedload(Equipment.location),
                joinedload(InstrumentReplacement.registered_by_user),
            )
            .order_by(InstrumentReplacement.replaced_at.desc())
        )
        stmt = apply_area_id_scope(stmt, current_user, InstrumentReplacement.area_id)
        return self.list(statement=stmt)

