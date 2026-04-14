from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.core.permissions import apply_area_id_scope
from app.models.equipment import Equipment
from app.models.instrument import Instrument
from app.models.instrument_replacement import InstrumentReplacement
from app.models.instrument_service_request import InstrumentServiceRequest
from app.models.user import User
from app.db.repositories.base import BaseRepository


class InstrumentServiceRequestRepository(BaseRepository[InstrumentServiceRequest]):
    model = InstrumentServiceRequest

    def get(self, entity_id) -> InstrumentServiceRequest | None:
        stmt = (
            select(InstrumentServiceRequest)
            .where(InstrumentServiceRequest.id == entity_id)
            .options(
                joinedload(InstrumentServiceRequest.instrument)
                .joinedload(Instrument.equipment)
                .joinedload(Equipment.area),
                joinedload(InstrumentServiceRequest.instrument)
                .joinedload(Instrument.equipment)
                .joinedload(Equipment.location),
                joinedload(InstrumentServiceRequest.instrument_replacement)
                .joinedload(InstrumentReplacement.removed_instrument)
                .joinedload(Instrument.equipment),
                joinedload(InstrumentServiceRequest.instrument_replacement)
                .joinedload(InstrumentReplacement.installed_instrument)
                .joinedload(Instrument.equipment),
                joinedload(InstrumentServiceRequest.registered_by_user),
            )
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_visible(self, current_user: User) -> list[InstrumentServiceRequest]:
        stmt = (
            select(InstrumentServiceRequest)
            .options(
                joinedload(InstrumentServiceRequest.instrument)
                .joinedload(Instrument.equipment)
                .joinedload(Equipment.area),
                joinedload(InstrumentServiceRequest.instrument)
                .joinedload(Instrument.equipment)
                .joinedload(Equipment.location),
                joinedload(InstrumentServiceRequest.instrument_replacement)
                .joinedload(InstrumentReplacement.removed_instrument)
                .joinedload(Instrument.equipment),
                joinedload(InstrumentServiceRequest.instrument_replacement)
                .joinedload(InstrumentReplacement.installed_instrument)
                .joinedload(Instrument.equipment),
                joinedload(InstrumentServiceRequest.registered_by_user),
            )
            .order_by(InstrumentServiceRequest.requested_at.desc())
        )
        stmt = apply_area_id_scope(stmt, current_user, InstrumentServiceRequest.area_id)
        return self.list(statement=stmt)

