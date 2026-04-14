from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session, joinedload

from app.core.enums import EquipmentStatus, RecordStatus
from app.models.collaborator import Collaborator
from app.models.equipment import Equipment
from app.models.location import Location
from app.models.movement import Movement
from app.models.user import User


@dataclass(frozen=True)
class MechanicalMetricSnapshot:
    equipment_count: int
    under_maintenance_count: int
    without_location_count: int
    active_collaborators_count: int


class MechanicalOverviewRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_metric_snapshot(self, area_id) -> MechanicalMetricSnapshot:
        collaborator_count_subquery = (
            select(func.count())
            .select_from(Collaborator)
            .where(Collaborator.area_id == area_id)
            .where(Collaborator.status == RecordStatus.ACTIVE)
            .scalar_subquery()
        )
        stmt = (
            select(
                func.count(Equipment.id),
                func.sum(
                    case(
                        (Equipment.status == EquipmentStatus.UNDER_MAINTENANCE, 1),
                        else_=0,
                    ),
                ),
                func.sum(
                    case(
                        (Equipment.location_id.is_(None), 1),
                        else_=0,
                    ),
                ),
                collaborator_count_subquery,
            )
            .select_from(Equipment)
            .where(Equipment.area_id == area_id)
        )
        row = self.db.execute(stmt).one()
        return MechanicalMetricSnapshot(
            equipment_count=int(row[0] or 0),
            under_maintenance_count=int(row[1] or 0),
            without_location_count=int(row[2] or 0),
            active_collaborators_count=int(row[3] or 0),
        )

    def list_status_summary(self, area_id) -> list[tuple[str, int]]:
        stmt = (
            select(Equipment.status, func.count(Equipment.id))
            .where(Equipment.area_id == area_id)
            .group_by(Equipment.status)
            .order_by(Equipment.status)
        )
        return [(row[0].value, int(row[1] or 0)) for row in self.db.execute(stmt).all()]

    def list_equipments(self, area_id, *, limit: int = 20) -> list[Equipment]:
        stmt = (
            select(Equipment)
            .where(Equipment.area_id == area_id)
            .options(joinedload(Equipment.location))
            .order_by(Equipment.code)
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars().all())

    def list_collaborators(self, area_id, *, limit: int = 20) -> list[Collaborator]:
        stmt = (
            select(Collaborator)
            .where(Collaborator.area_id == area_id)
            .order_by(Collaborator.full_name)
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars().all())

    def list_recent_movements(self, area_id, *, limit: int = 8) -> list[tuple]:
        stmt = (
            select(
                Equipment.code,
                Equipment.description,
                Location.name,
                Movement.moved_at,
                User.full_name,
                Movement.reason,
                Movement.status_after,
            )
            .select_from(Movement)
            .join(Movement.equipment)
            .join(Movement.moved_by_user)
            .join(Location, Location.id == Movement.new_location_id, isouter=True)
            .where(Equipment.area_id == area_id)
            .order_by(Movement.moved_at.desc())
            .limit(limit)
        )
        return list(self.db.execute(stmt).all())

