from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.core.security import get_password_hash
from app.core.enums import AreaCode, EquipmentStatus, EquipmentType, RecordStatus, RoleName
from app.models.area import Area
from app.db.base import Base
from app.models.collaborator import Collaborator
from app.models.equipment import Equipment
from app.models.location import Location
from app.models.movement import Movement
from app.models.role import Role
from app.models.user import User
from app.models.user_area import UserArea
from app.services.mechanical import MechanicalService


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


def _create_user(session: Session, *, role: Role, email: str, area_ids: list | None = None) -> User:
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


def test_build_overview_returns_mechanical_data(db_session: Session) -> None:
    supervisor_role = _create_role(db_session, RoleName.SUPERVISOR)
    mechanical_area = _create_area(db_session, name="Mecanica", code=AreaCode.MECANICA)
    actor = _create_user(
        db_session,
        role=supervisor_role,
        email="supervisor@example.com",
        area_ids=[mechanical_area.id],
    )
    location = Location(name="Oficina Mecanica", sector="OFICINA", description=None, area_id=mechanical_area.id)
    db_session.add(location)
    db_session.flush()

    equipment = Equipment(
        code="MEQ-001",
        tag="P-1001",
        description="Bomba centrifuga",
        sector="OFICINA",
        manufacturer=None,
        model=None,
        serial_number=None,
        notes=None,
        type=EquipmentType.GENERIC,
        status=EquipmentStatus.UNDER_MAINTENANCE,
        registered_at=datetime.now(UTC),
        area_id=mechanical_area.id,
        location_id=location.id,
    )
    collaborator = Collaborator(
        full_name="Carlos Mecanico",
        registration_number="MEC-001",
        job_title="Mecanico",
        contact_phone=None,
        status=RecordStatus.ACTIVE,
        area_id=mechanical_area.id,
    )
    db_session.add_all([equipment, collaborator])
    db_session.flush()

    movement = Movement(
        equipment_id=equipment.id,
        previous_location_id=None,
        new_location_id=location.id,
        moved_by_user_id=actor.id,
        moved_at=datetime.now(UTC),
        reason="Entrada na oficina mecanica",
        status_after=EquipmentStatus.UNDER_MAINTENANCE.value,
        notes=None,
    )
    db_session.add(movement)
    db_session.commit()

    overview = MechanicalService(db_session).build_overview(actor)
    metrics = {item.label: item.value for item in overview.metrics}

    assert overview.area_name == "Mecanica"
    assert metrics["Equipamentos mecanicos"] == 1
    assert metrics["Em manutencao"] == 1
    assert metrics["Equipe ativa"] == 1
    assert overview.equipments[0].code == "MEQ-001"
    assert overview.collaborators[0].full_name == "Carlos Mecanico"
    assert overview.recent_movements[0].equipment_code == "MEQ-001"


def test_build_overview_hides_collaborator_details_for_level_one_role(db_session: Session) -> None:
    manutentor_role = _create_role(db_session, RoleName.MANUTENTOR)
    mechanical_area = _create_area(db_session, name="Mecanica", code=AreaCode.MECANICA)
    actor = _create_user(
        db_session,
        role=manutentor_role,
        email="manutentor@example.com",
        area_ids=[mechanical_area.id],
    )
    location = Location(name="Oficina Mecanica", sector="OFICINA", description=None, area_id=mechanical_area.id)
    db_session.add(location)
    db_session.flush()

    equipment = Equipment(
        code="MEQ-002",
        tag="P-1002",
        description="Compressor mecanico",
        sector="OFICINA",
        manufacturer=None,
        model=None,
        serial_number=None,
        notes=None,
        type=EquipmentType.GENERIC,
        status=EquipmentStatus.ACTIVE,
        registered_at=datetime.now(UTC),
        area_id=mechanical_area.id,
        location_id=location.id,
    )
    collaborator = Collaborator(
        full_name="Equipe Oculta",
        registration_number="MEC-002",
        job_title="Mecanico",
        contact_phone=None,
        status=RecordStatus.ACTIVE,
        area_id=mechanical_area.id,
    )
    db_session.add_all([equipment, collaborator])
    db_session.commit()

    overview = MechanicalService(db_session).build_overview(actor)
    metrics = {item.label: item.value for item in overview.metrics}

    assert metrics["Equipe ativa"] == 1
    assert overview.collaborators == []


def test_build_overview_rejects_user_outside_mechanical_area(db_session: Session) -> None:
    supervisor_role = _create_role(db_session, RoleName.SUPERVISOR)
    outsider_area = _create_area(db_session, name="Eletrica", code=AreaCode.ELETRICA)
    _create_area(db_session, name="Mecanica", code=AreaCode.MECANICA)
    actor = _create_user(
        db_session,
        role=supervisor_role,
        email="supervisor@example.com",
        area_ids=[outsider_area.id],
    )

    with pytest.raises(HTTPException) as exc_info:
        MechanicalService(db_session).build_overview(actor)

    assert exc_info.value.detail == "User does not have permission for the requested area."


def test_build_overview_uses_compact_query_budget(db_session: Session) -> None:
    supervisor_role = _create_role(db_session, RoleName.SUPERVISOR)
    mechanical_area = _create_area(db_session, name="Mecanica", code=AreaCode.MECANICA)
    actor = _create_user(
        db_session,
        role=supervisor_role,
        email="supervisor.performance@example.com",
        area_ids=[mechanical_area.id],
    )
    location = Location(name="Oficina Performance", sector="OFICINA", description=None, area_id=mechanical_area.id)
    db_session.add(location)
    db_session.flush()

    equipment = Equipment(
        code="MEQ-PERF",
        tag="P-9001",
        description="Bomba de teste",
        sector="OFICINA",
        manufacturer=None,
        model=None,
        serial_number=None,
        notes=None,
        type=EquipmentType.GENERIC,
        status=EquipmentStatus.ACTIVE,
        registered_at=datetime.now(UTC),
        area_id=mechanical_area.id,
        location_id=location.id,
    )
    collaborator = Collaborator(
        full_name="Mecanico Performance",
        registration_number="MEC-PERF",
        job_title="Mecanico",
        contact_phone=None,
        status=RecordStatus.ACTIVE,
        area_id=mechanical_area.id,
    )
    db_session.add_all([equipment, collaborator])
    db_session.commit()
    _ = actor.permissions
    _ = actor.area_ids

    query_count = _count_queries(
        db_session,
        lambda: MechanicalService(db_session).build_overview(actor),
    )

    assert query_count <= 6

