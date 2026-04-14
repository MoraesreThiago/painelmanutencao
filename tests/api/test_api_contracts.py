from __future__ import annotations

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import get_db
from app.core.security import get_password_hash
from app.core.enums import AreaCode, EquipmentStatus, EquipmentType, RecordStatus, RoleName
from app.core.notification_events import NotificationEventType
from app.main import app
from app.models.area import Area
from app.db.base import Base
from app.models.collaborator import Collaborator
from app.models.equipment import Equipment
from app.models.location import Location
from app.models.role import Role
from app.models.user import User
from app.models.user_area import UserArea
from app.services.notification import NotificationDispatchService, NotificationService


@pytest.fixture
def db_session() -> Session:
    engine = create_engine(
        "sqlite+pysqlite://",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    testing_session = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)

    with testing_session() as session:
        yield session

    engine.dispose()


@pytest.fixture
def client(db_session: Session, monkeypatch: pytest.MonkeyPatch):
    def override_get_db():
        yield db_session

    monkeypatch.setattr("app.main.settings.auto_seed", False)
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


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


def _login(client: TestClient, *, email: str, password: str = "secret") -> dict[str, str]:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_mechanical_overview_endpoint_respects_area_scope(client: TestClient, db_session: Session) -> None:
    supervisor_role = _create_role(db_session, RoleName.SUPERVISOR)
    mechanical_area = _create_area(db_session, name="Mecanica", code=AreaCode.MECANICA)
    actor = _create_user(
        db_session,
        role=supervisor_role,
        email="supervisor@example.com",
        area_ids=[mechanical_area.id],
    )
    location = Location(name="Oficina API", sector="OFICINA", description=None, area_id=mechanical_area.id)
    db_session.add(location)
    db_session.flush()
    db_session.add(
        Equipment(
            code="MEQ-API",
            tag="P-API",
            description="Bomba API",
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
        ),
    )
    db_session.commit()

    headers = _login(client, email=actor.email)
    response = client.get("/api/v1/mechanical/overview", headers=headers)

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["area_name"] == "Mecanica"
    assert payload["equipments"][0]["code"] == "MEQ-API"


def test_notification_events_endpoint_filters_by_status_and_event_type(
    client: TestClient,
    db_session: Session,
) -> None:
    supervisor_role = _create_role(db_session, RoleName.SUPERVISOR)
    area = _create_area(db_session, name="Mecanica", code=AreaCode.MECANICA)
    actor = _create_user(
        db_session,
        role=supervisor_role,
        email="supervisor@example.com",
        area_ids=[area.id],
    )

    event_service = NotificationService(db_session)
    dispatch_service = NotificationDispatchService(db_session)
    created_event = event_service.enqueue(
        event_type=NotificationEventType.MOTOR_CREATED,
        entity_name="Motor",
        entity_id="motor-100",
        area_id=area.id,
        payload={"code": "MO-100"},
    )
    failed_event = event_service.enqueue(
        event_type=NotificationEventType.MOVEMENT_RECORDED,
        entity_name="Equipment",
        entity_id="eq-200",
        area_id=area.id,
        payload={"equipment_code": "EQ-200"},
    )
    dispatch_service.mark_error(failed_event.id, error_message="temporary")
    db_session.commit()

    headers = _login(client, email=actor.email)
    response = client.get(
        "/api/v1/notification-events",
        params={"status": "PENDING", "event_type": "motor.created"},
        headers=headers,
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["entity_id"] == created_event.entity_id
    assert payload[0]["status"] == "PENDING"


def test_supervisor_cannot_delete_collaborator_physically(client: TestClient, db_session: Session) -> None:
    supervisor_role = _create_role(db_session, RoleName.SUPERVISOR)
    area = _create_area(db_session, name="Eletrica", code=AreaCode.ELETRICA)
    actor = _create_user(
        db_session,
        role=supervisor_role,
        email="supervisor.delete@example.com",
        area_ids=[area.id],
    )
    collaborator = Collaborator(
        full_name="Colaborador Teste",
        registration_number="COL-DELETE-001",
        job_title="Tecnico",
        contact_phone=None,
        status=RecordStatus.ACTIVE,
        area_id=area.id,
    )
    db_session.add(collaborator)
    db_session.commit()

    headers = _login(client, email=actor.email)
    response = client.delete(f"/api/v1/collaborators/{collaborator.id}", headers=headers)

    assert response.status_code == 403, response.text


def test_maintainer_cannot_access_collaborator_management_endpoint(
    client: TestClient,
    db_session: Session,
) -> None:
    manutentor_role = _create_role(db_session, RoleName.MANUTENTOR)
    area = _create_area(db_session, name="Mecanica", code=AreaCode.MECANICA)
    actor = _create_user(
        db_session,
        role=manutentor_role,
        email="manutentor.collab@example.com",
        area_ids=[area.id],
    )

    headers = _login(client, email=actor.email)
    response = client.get("/api/v1/collaborators", headers=headers)

    assert response.status_code == 403, response.text

