from __future__ import annotations

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.security import get_password_hash
from app.core.enums import AreaCode, NotificationStatus, RoleName
from app.core.notification_events import NotificationEventType
from app.models.area import Area
from app.db.base import Base
from app.models.role import Role
from app.models.user import User
from app.models.user_area import UserArea
from app.services.notification import NotificationDispatchService, NotificationService


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


def test_list_visible_scopes_notification_events_by_area(db_session: Session) -> None:
    supervisor_role = _create_role(db_session, RoleName.SUPERVISOR)
    area_a = _create_area(db_session, name="Mecanica", code=AreaCode.MECANICA)
    area_b = _create_area(db_session, name="Eletrica", code=AreaCode.ELETRICA)
    actor = _create_user(
        db_session,
        role=supervisor_role,
        email="supervisor@example.com",
        area_ids=[area_a.id],
    )

    service = NotificationService(db_session)
    service.enqueue(
        event_type=NotificationEventType.MOVEMENT_RECORDED,
        entity_name="Equipment",
        entity_id="EQ-A",
        area_id=area_a.id,
        payload={"equipment_code": "EQ-A"},
    )
    service.enqueue(
        event_type=NotificationEventType.MOVEMENT_RECORDED,
        entity_name="Equipment",
        entity_id="EQ-B",
        area_id=area_b.id,
        payload={"equipment_code": "EQ-B"},
    )

    visible_events = service.list_visible(actor)

    assert len(visible_events) == 1
    assert visible_events[0].entity_id == "EQ-A"


def test_dispatch_service_tracks_attempts_errors_and_processing(db_session: Session) -> None:
    area = _create_area(db_session, name="Mecanica", code=AreaCode.MECANICA)
    service = NotificationService(db_session)
    dispatch_service = NotificationDispatchService(db_session)
    event = service.enqueue(
        event_type=NotificationEventType.MOTOR_CREATED,
        entity_name="Motor",
        entity_id="motor-1",
        area_id=area.id,
        payload={"code": "MO-001"},
    )

    pending = dispatch_service.list_pending()
    assert pending[0].id == event.id
    assert pending[0].status == NotificationStatus.PENDING

    failed = dispatch_service.mark_error(event.id, error_message="temporary downstream failure")
    assert failed.status == NotificationStatus.ERROR
    assert failed.processing_attempts == 1
    assert failed.last_error == "temporary downstream failure"
    assert failed.last_attempted_at is not None

    requeued = dispatch_service.requeue(event.id)
    assert requeued.status == NotificationStatus.PENDING
    assert requeued.last_error is None

    processed = dispatch_service.mark_processed(event.id)
    assert processed.status == NotificationStatus.PROCESSED
    assert processed.processing_attempts == 2
    assert processed.processed_at is not None
    assert processed.last_attempted_at is not None


def test_dispatch_service_rejects_invalid_transitions(db_session: Session) -> None:
    area = _create_area(db_session, name="Mecanica", code=AreaCode.MECANICA)
    service = NotificationService(db_session)
    dispatch_service = NotificationDispatchService(db_session)
    event = service.enqueue(
        event_type=NotificationEventType.MOTOR_CREATED,
        entity_name="Motor",
        entity_id="motor-2",
        area_id=area.id,
        payload={"code": "MO-002"},
    )

    processed = dispatch_service.mark_processed(event.id)
    assert processed.status == NotificationStatus.PROCESSED

    with pytest.raises(HTTPException) as processed_again:
        dispatch_service.mark_processed(event.id)
    assert processed_again.value.status_code == 409

    with pytest.raises(HTTPException) as requeue_processed:
        dispatch_service.requeue(event.id)
    assert requeue_processed.value.status_code == 409


def test_list_visible_filters_notification_events(db_session: Session) -> None:
    supervisor_role = _create_role(db_session, RoleName.SUPERVISOR)
    area = _create_area(db_session, name="Mecanica", code=AreaCode.MECANICA)
    actor = _create_user(
        db_session,
        role=supervisor_role,
        email="supervisor@example.com",
        area_ids=[area.id],
    )
    service = NotificationService(db_session)
    dispatch_service = NotificationDispatchService(db_session)

    event_a = service.enqueue(
        event_type=NotificationEventType.MOTOR_CREATED,
        entity_name="Motor",
        entity_id="motor-a",
        area_id=area.id,
        payload={"code": "MO-A"},
    )
    event_b = service.enqueue(
        event_type=NotificationEventType.MOVEMENT_RECORDED,
        entity_name="Equipment",
        entity_id="movement-b",
        area_id=area.id,
        payload={"equipment_code": "EQ-B"},
    )
    dispatch_service.mark_error(event_b.id, error_message="failed")

    filtered_by_type = service.list_visible(actor, event_type=NotificationEventType.MOTOR_CREATED)
    filtered_by_status = service.list_visible(actor, status_filter=NotificationStatus.ERROR)

    assert [event.entity_id for event in filtered_by_type] == [event_a.entity_id]
    assert [event.entity_id for event in filtered_by_status] == [event_b.entity_id]

