from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.enums import AreaCode
from app.core.permissions import PermissionName, ensure_area_access, ensure_permission, has_permission
from app.db.repositories.areas import AreaRepository
from app.db.repositories.mechanical import MechanicalOverviewRepository
from app.schemas.mechanical import (
    MechanicalCollaboratorItem,
    MechanicalEquipmentItem,
    MechanicalMetric,
    MechanicalOverviewRead,
    MechanicalRecentMovement,
    MechanicalStatusSummary,
)


class MechanicalService:
    def __init__(self, db: Session):
        self.db = db
        self.area_repository = AreaRepository(db)
        self.repository = MechanicalOverviewRepository(db)

    def build_overview(self, current_user) -> MechanicalOverviewRead:
        ensure_permission(current_user, PermissionName.VIEW_AREA_DATA)
        mechanical_area = self.area_repository.get_by_code(AreaCode.MECANICA)
        if mechanical_area is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Mechanical area is not configured.",
            )

        ensure_area_access(current_user, mechanical_area.id)
        area_id = mechanical_area.id
        metric_snapshot = self.repository.get_metric_snapshot(area_id)

        metrics = [
            MechanicalMetric(
                label="Equipamentos mecanicos",
                value=metric_snapshot.equipment_count,
            ),
            MechanicalMetric(
                label="Em manutencao",
                value=metric_snapshot.under_maintenance_count,
            ),
            MechanicalMetric(
                label="Sem localizacao",
                value=metric_snapshot.without_location_count,
            ),
            MechanicalMetric(
                label="Equipe ativa",
                value=metric_snapshot.active_collaborators_count,
            ),
        ]

        status_summary = [
            MechanicalStatusSummary(status=status_name, total=total)
            for status_name, total in self.repository.list_status_summary(area_id)
        ]

        equipments = [
            MechanicalEquipmentItem(
                id=item.id,
                code=item.code,
                tag=item.tag,
                description=item.description,
                sector=item.sector,
                status=item.status.value,
                location_name=item.location.name if item.location else None,
            )
            for item in self.repository.list_equipments(area_id)
        ]

        collaborators: list[MechanicalCollaboratorItem] = []
        if has_permission(current_user, PermissionName.MANAGE_AREA_DATA):
            collaborators = [
                MechanicalCollaboratorItem(
                    id=item.id,
                    full_name=item.full_name,
                    registration_number=item.registration_number,
                    job_title=item.job_title,
                    contact_phone=item.contact_phone,
                    status=item.status.value,
                )
                for item in self.repository.list_collaborators(area_id)
            ]

        recent_movements = [
            MechanicalRecentMovement(
                equipment_code=row[0],
                equipment_description=row[1],
                new_location=row[2],
                moved_at=row[3],
                moved_by=row[4],
                reason=row[5],
                status_after=row[6],
            )
            for row in self.repository.list_recent_movements(area_id)
        ]

        return MechanicalOverviewRead(
            area_name=mechanical_area.name,
            metrics=metrics,
            status_summary=status_summary,
            equipments=equipments,
            collaborators=collaborators,
            recent_movements=recent_movements,
        )

