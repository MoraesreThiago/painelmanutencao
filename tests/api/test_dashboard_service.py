from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.core.security import get_password_hash
from app.core.enums import AreaCode, EquipmentStatus, EquipmentType, RoleName
from app.models.area import Area
from app.db.base import Base
from app.models.equipment import Equipment
from app.models.location import Location
from app.models.role import Role
from app.models.user import User
from app.models.user_area import UserArea
from app.services.dashboard import DashboardService


@pytest.fixture
def db_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    testing_session = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)

    with testing_session() as session:
        yield session

    engine.dispose()


def _create_role(session: Session, role_name: RoleName) -> Role:
    role = Role(name=role_name, description=f"{role_name.value} role")
    session.add(role)
    session.flush()
    return role


def _create_area(session: Session, *, name: str, code: AreaCode) -> Area:
    area = Area(name=name, code=code, description=f"Area {name}")
    session.add(area)
    session.flush()
    return area


def _create_user(
    session: Session,
    *,
    role: Role,
    email: str,
    area_ids: list | None = None,
) -> User:
    user = User(
        full_name=email,
        email=email,
        password_hash=get_password_hash("secret"),
        role_id=role.id,
        role=role,
        area_id=area_ids[0] if area_ids else None,
    )
    session.add(user)
    session.flush()

    for area_id in area_ids or []:
        session.add(UserArea(user_id=user.id, area_id=area_id))

    session.flush()
    session.refresh(user)
    return user


def _create_location(session: Session, *, area: Area, name: str) -> Location:
    location = Location(name=name, sector="SECTOR-1", description=None, area_id=area.id, area=area)
    session.add(location)
    session.flush()
    return location


def _create_equipment(session: Session, *, area: Area, location: Location, code: str) -> Equipment:
    equipment = Equipment(
        code=code,
        tag=None,
        description=f"Equipment {code}",
        sector="SECTOR-1",
        manufacturer=None,
        model=None,
        serial_number=None,
        notes=None,
        type=EquipmentType.GENERIC,
        status=EquipmentStatus.ACTIVE,
        registered_at=datetime.now(UTC),
        area_id=area.id,
        location_id=location.id,
        area=area,
        location=location,
    )
    session.add(equipment)
    session.flush()
    return equipment


def _count_queries(session: Session, callback) -> int:
    bind = session.get_bind()
    counter: Counter[str] = Counter()

    def before_cursor_execute(*_args, **_kwargs) -> None:
        counter["queries"] += 1

    event.listen(bind, "before_cursor_execute", before_cursor_execute)
    try:
        callback()
    finally:
        event.remove(bind, "before_cursor_execute", before_cursor_execute)
    return counter["queries"]


def test_build_dashboard_respects_explicit_area_scope(db_session: Session) -> None:
    supervisor_role = _create_role(db_session, RoleName.SUPERVISOR)
    area_a = _create_area(db_session, name="Eletrica", code=AreaCode.ELETRICA)
    area_b = _create_area(db_session, name="Instrumentacao", code=AreaCode.INSTRUMENTACAO)
    actor = _create_user(
        db_session,
        role=supervisor_role,
        email="supervisor@example.com",
        area_ids=[area_a.id, area_b.id],
    )
    location_a = _create_location(db_session, area=area_a, name="ELE-L1")
    location_b = _create_location(db_session, area=area_b, name="INS-L1")
    _create_equipment(db_session, area=area_a, location=location_a, code="EQ-A")
    _create_equipment(db_session, area=area_b, location=location_b, code="EQ-B")

    dashboard = DashboardService(db_session).build_dashboard(actor, area_id=area_a.id)
    metrics = {item.label: item.value for item in dashboard.metrics}

    assert metrics["Total de equipamentos"] == 1
    assert dashboard.area_summary[0].area_name == "Eletrica"
    assert len(dashboard.area_summary) == 1


def test_build_dashboard_rejects_outside_area_scope(db_session: Session) -> None:
    supervisor_role = _create_role(db_session, RoleName.SUPERVISOR)
    actor_area = _create_area(db_session, name="Mecanica", code=AreaCode.MECANICA)
    outsider_area = _create_area(db_session, name="Eletrica", code=AreaCode.ELETRICA)
    actor = _create_user(
        db_session,
        role=supervisor_role,
        email="supervisor@example.com",
        area_ids=[actor_area.id],
    )

    with pytest.raises(HTTPException) as exc_info:
        DashboardService(db_session).build_dashboard(actor, area_id=outsider_area.id)

    assert exc_info.value.detail == "User does not have permission for the requested area."


def test_build_dashboard_uses_compact_query_budget(db_session: Session) -> None:
    manager_role = _create_role(db_session, RoleName.GERENTE)
    area = _create_area(db_session, name="Mecanica", code=AreaCode.MECANICA)
    actor = _create_user(
        db_session,
        role=manager_role,
        email="gerente@example.com",
        area_ids=[area.id],
    )
    location = _create_location(db_session, area=area, name="MEC-L1")
    _create_equipment(db_session, area=area, location=location, code="EQ-M-001")
    db_session.commit()

    query_count = _count_queries(
        db_session,
        lambda: DashboardService(db_session).build_dashboard(actor),
    )

    assert query_count <= 6

