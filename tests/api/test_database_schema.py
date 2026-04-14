from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, inspect

import app.db.database as database_module


def test_create_all_bootstraps_expected_schema(tmp_path: Path) -> None:
    database_path = tmp_path / "schema_bootstrap.db"
    engine = create_engine(f"sqlite+pysqlite:///{database_path.as_posix()}", future=True)
    original_engine = database_module.engine

    database_module.engine = engine
    try:
        database_module.create_all()
        tables = set(inspect(engine).get_table_names())
    finally:
        database_module.engine = original_engine
        engine.dispose()

    expected_tables = {
        "areas",
        "audit_logs",
        "collaborators",
        "equipments",
        "external_service_orders",
        "instruments",
        "locations",
        "motors",
        "movements",
        "notification_events",
        "roles",
        "user_areas",
        "users",
    }

    assert expected_tables.issubset(tables)
