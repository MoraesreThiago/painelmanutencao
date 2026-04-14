from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.core.enums import EquipmentStatus, EquipmentType, ExternalServiceStatus, InstrumentStatus
from app.core.permissions import (
    PermissionName,
    apply_area_id_scope,
    ensure_area_access,
    ensure_permission,
)
from app.models.area import Area
from app.models.equipment import Equipment
from app.models.external_service_order import ExternalServiceOrder
from app.models.instrument import Instrument
from app.models.location import Location
from app.models.movement import Movement
from app.models.user import User
from app.schemas.dashboard import (
    AreaSummary,
    DashboardAlert,
    DashboardMetric,
    DashboardRead,
    RecentMovement,
)


class DashboardService:
    def __init__(self, db: Session):
        self.db = db

    def _count(self, stmt):
        return int(self.db.execute(stmt).scalar_one() or 0)

    @staticmethod
    def _scope_query(stmt, current_user: User, area_column, area_id: UUID | None):
        if area_id is not None:
            return stmt.where(area_column == area_id)
        return apply_area_id_scope(stmt, current_user, area_column)

    def build_dashboard(self, current_user: User, *, area_id: UUID | None = None) -> DashboardRead:
        ensure_permission(current_user, PermissionName.VIEW_DASHBOARD)
        if area_id is not None:
            ensure_area_access(current_user, area_id)

        now = datetime.now(UTC)
        equipment_metrics_stmt = select(
            func.count(Equipment.id),
            func.sum(case((Equipment.type == EquipmentType.MOTOR, 1), else_=0)),
            func.sum(case((Equipment.type == EquipmentType.INSTRUMENT, 1), else_=0)),
            func.sum(case((Equipment.status == EquipmentStatus.EXTERNAL_SERVICE, 1), else_=0)),
        )
        equipment_metrics_stmt = self._scope_query(
            equipment_metrics_stmt,
            current_user,
            Equipment.area_id,
            area_id,
        )
        equipment_metrics_row = self.db.execute(equipment_metrics_stmt).one()
        equipment_count = int(equipment_metrics_row[0] or 0)
        motor_count = int(equipment_metrics_row[1] or 0)
        instrument_count = int(equipment_metrics_row[2] or 0)
        external_count = int(equipment_metrics_row[3] or 0)

        overdue_returns_stmt = (
            select(func.count())
            .select_from(ExternalServiceOrder)
            .join(ExternalServiceOrder.motor)
            .join(Equipment, Equipment.id == ExternalServiceOrder.motor_id)
            .where(ExternalServiceOrder.expected_return_at < now)
            .where(ExternalServiceOrder.service_status != ExternalServiceStatus.RETURNED)
        )
        overdue_returns_stmt = self._scope_query(
            overdue_returns_stmt,
            current_user,
            Equipment.area_id,
            area_id,
        )

        area_summary_stmt = (
            select(
                Area.name,
                func.count(Equipment.id).label("equipment_count"),
                func.sum(case((Equipment.type == EquipmentType.MOTOR, 1), else_=0)).label(
                    "motor_count",
                ),
                func.sum(
                    case((Equipment.type == EquipmentType.INSTRUMENT, 1), else_=0),
                ).label("instrument_count"),
            )
            .join(Equipment, Equipment.area_id == Area.id)
            .group_by(Area.name)
            .order_by(Area.name)
        )
        area_summary_stmt = self._scope_query(area_summary_stmt, current_user, Area.id, area_id)

        recent_movements_stmt = (
            select(
                Equipment.code,
                Equipment.description,
                Location.name,
                Movement.moved_at,
                User.full_name,
                Movement.reason,
            )
            .join(Movement.equipment)
            .join(Movement.moved_by_user)
            .join(Location, Location.id == Movement.new_location_id, isouter=True)
            .order_by(Movement.moved_at.desc())
            .limit(8)
        )
        recent_movements_stmt = self._scope_query(
            recent_movements_stmt,
            current_user,
            Equipment.area_id,
            area_id,
        )

        calibration_due_stmt = (
            select(func.count())
            .select_from(Instrument)
            .join(Instrument.equipment)
            .where(Instrument.calibration_due_date <= (now + timedelta(days=30)).date())
            .where(Instrument.current_status != InstrumentStatus.INACTIVE)
        )
        calibration_due_stmt = self._scope_query(
            calibration_due_stmt,
            current_user,
            Equipment.area_id,
            area_id,
        )
        overdue_count = self._count(overdue_returns_stmt)
        calibration_due_count = self._count(calibration_due_stmt)

        metrics = [
            DashboardMetric(label="Total de equipamentos", value=equipment_count),
            DashboardMetric(label="Total de motores", value=motor_count),
            DashboardMetric(label="Total de instrumentos", value=instrument_count),
            DashboardMetric(
                label="Itens em servico externo",
                value=external_count,
            ),
            DashboardMetric(
                label="Retornos atrasados",
                value=overdue_count,
            ),
        ]

        area_summary = [
            AreaSummary(
                area_name=row[0],
                equipment_count=int(row[1] or 0),
                motor_count=int(row[2] or 0),
                instrument_count=int(row[3] or 0),
            )
            for row in self.db.execute(area_summary_stmt).all()
        ]

        recent_movements = [
            RecentMovement(
                equipment_code=row[0],
                equipment_description=row[1],
                new_location=row[2],
                moved_at=row[3],
                moved_by=row[4],
                reason=row[5],
            )
            for row in self.db.execute(recent_movements_stmt).all()
        ]

        alerts: list[DashboardAlert] = []
        if overdue_count:
            alerts.append(
                DashboardAlert(
                    title="Retornos atrasados",
                    description=f"{overdue_count} ordem(ns) externas estao com retorno atrasado.",
                    severity="high",
                ),
            )
        if external_count:
            alerts.append(
                DashboardAlert(
                    title="Itens fora da planta",
                    description=f"{external_count} item(ns) estao em servico externo.",
                    severity="medium",
                ),
            )
        if calibration_due_count:
            alerts.append(
                DashboardAlert(
                    title="Calibracoes proximas",
                    description=f"{calibration_due_count} instrumento(s) com calibracao proxima.",
                    severity="medium",
                ),
            )
        if not alerts:
            alerts.append(
                DashboardAlert(
                    title="Operacao estavel",
                    description="Nao ha alertas criticos no momento.",
                    severity="low",
                ),
            )

        return DashboardRead(
            metrics=metrics,
            area_summary=area_summary,
            recent_movements=recent_movements,
            alerts=alerts,
        )

