from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.core.permissions import apply_area_id_scope
from app.models.equipment import Equipment
from app.models.external_service_order import ExternalServiceOrder
from app.models.motor import Motor
from app.models.user import User
from app.db.repositories.base import BaseRepository


class ExternalServiceOrderRepository(BaseRepository[ExternalServiceOrder]):
    model = ExternalServiceOrder

    def get(self, entity_id) -> ExternalServiceOrder | None:
        stmt = (
            select(ExternalServiceOrder)
            .where(ExternalServiceOrder.id == entity_id)
            .options(
                joinedload(ExternalServiceOrder.motor)
                .joinedload(Motor.equipment)
                .joinedload(Equipment.area),
                joinedload(ExternalServiceOrder.motor)
                .joinedload(Motor.equipment)
                .joinedload(Equipment.location),
                joinedload(ExternalServiceOrder.authorized_by_user),
                joinedload(ExternalServiceOrder.registered_by_user),
            )
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_visible(self, current_user: User) -> list[ExternalServiceOrder]:
        stmt = (
            select(ExternalServiceOrder)
            .join(ExternalServiceOrder.motor)
            .join(Motor.equipment)
            .options(
                joinedload(ExternalServiceOrder.motor)
                .joinedload(Motor.equipment)
                .joinedload(Equipment.area),
                joinedload(ExternalServiceOrder.motor)
                .joinedload(Motor.equipment)
                .joinedload(Equipment.location),
                joinedload(ExternalServiceOrder.authorized_by_user),
                joinedload(ExternalServiceOrder.registered_by_user),
            )
            .order_by(ExternalServiceOrder.sent_at.desc())
        )
        stmt = apply_area_id_scope(stmt, current_user, Equipment.area_id)
        return self.list(statement=stmt)

