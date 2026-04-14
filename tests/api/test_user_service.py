from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.security import get_password_hash
from app.core.enums import AreaCode, RoleName
from app.models.area import Area
from app.db.base import Base
from app.models.role import Role
from app.models.user import User
from app.models.user_area import UserArea
from app.schemas.user import UserCreate, UserUpdate
from app.services.users import UserService


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


def test_create_user_syncs_multiple_area_assignments(db_session: Session) -> None:
    admin_role = _create_role(db_session, RoleName.ADMIN)
    manutentor_role = _create_role(db_session, RoleName.MANUTENTOR)
    area_a = _create_area(db_session, name="Eletrica", code=AreaCode.ELETRICA)
    area_b = _create_area(db_session, name="Instrumentacao", code=AreaCode.INSTRUMENTACAO)
    actor = _create_user(db_session, role=admin_role, email="admin@example.com")

    service = UserService(db_session)
    created = service.create_user(
        UserCreate(
            full_name="Tecnico Multi Area",
            email="tecnico@example.com",
            registration_number="TEC-001",
            job_title="Tecnico",
            phone=None,
            is_active=True,
            role_id=manutentor_role.id,
            area_id=area_a.id,
            area_ids=[area_a.id, area_b.id],
            password="Strong@123",
        ),
        actor,
    )

    assert created.area_id == area_a.id
    assert {str(area.id) for area in created.allowed_areas} == {str(area_a.id), str(area_b.id)}


def test_supervisor_cannot_create_users_without_manage_permission(db_session: Session) -> None:
    supervisor_role = _create_role(db_session, RoleName.SUPERVISOR)
    gerente_role = _create_role(db_session, RoleName.GERENTE)
    area = _create_area(db_session, name="Mecanica", code=AreaCode.MECANICA)
    actor = _create_user(
        db_session,
        role=supervisor_role,
        email="supervisor@example.com",
        area_ids=[area.id],
    )

    service = UserService(db_session)

    with pytest.raises(HTTPException) as exc_info:
        service.create_user(
            UserCreate(
                full_name="Gerente Novo",
                email="gerente@example.com",
                registration_number="GER-001",
                job_title="Gerente",
                phone=None,
                is_active=True,
                role_id=gerente_role.id,
                area_id=None,
                area_ids=None,
                password="Strong@123",
            ),
            actor,
        )

    assert exc_info.value.detail == "User does not have permission for this action."


def test_update_user_resyncs_multiple_area_assignments(db_session: Session) -> None:
    admin_role = _create_role(db_session, RoleName.ADMIN)
    manutentor_role = _create_role(db_session, RoleName.MANUTENTOR)
    area_a = _create_area(db_session, name="Eletrica", code=AreaCode.ELETRICA)
    area_b = _create_area(db_session, name="Mecanica", code=AreaCode.MECANICA)
    area_c = _create_area(db_session, name="Instrumentacao", code=AreaCode.INSTRUMENTACAO)
    actor = _create_user(db_session, role=admin_role, email="admin@example.com")
    target = _create_user(
        db_session,
        role=manutentor_role,
        email="target@example.com",
        area_ids=[area_a.id, area_b.id],
    )

    service = UserService(db_session)
    updated = service.update_user(
        target.id,
        UserUpdate(
            area_id=area_c.id,
            area_ids=[area_c.id],
        ),
        actor,
    )

    assert updated.area_id == area_c.id
    assert {str(area.id) for area in updated.allowed_areas} == {str(area_c.id)}


def test_gerente_can_view_any_user_record(db_session: Session) -> None:
    gerente_role = _create_role(db_session, RoleName.GERENTE)
    manutentor_role = _create_role(db_session, RoleName.MANUTENTOR)
    area = _create_area(db_session, name="Eletrica", code=AreaCode.ELETRICA)
    actor = _create_user(db_session, role=gerente_role, email="gerente@example.com")
    target = _create_user(
        db_session,
        role=manutentor_role,
        email="target@example.com",
        area_ids=[area.id],
    )

    service = UserService(db_session)
    visible = service.get_user(target.id, actor)

    assert visible.id == target.id

