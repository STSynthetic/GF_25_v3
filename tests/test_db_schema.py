from __future__ import annotations

from sqlalchemy import create_engine, inspect

from app.db import schema


def test_schema_tables_and_foreign_keys_sqlite_memory():
    # Use in-memory SQLite to validate DDL shape without requiring Postgres
    engine = create_engine("sqlite:///:memory:")

    # Create all tables
    schema.create_all(engine)

    insp = inspect(engine)

    # Tables exist
    tables = set(insp.get_table_names())
    assert {"tasks", "processing_state", "qa_attempts", "audit_logs"}.issubset(tables)

    # Foreign keys
    fks_processing = insp.get_foreign_keys("processing_state")
    assert any(fk.get("referred_table") == "tasks" for fk in fks_processing)

    fks_qa = insp.get_foreign_keys("qa_attempts")
    assert any(fk.get("referred_table") == "tasks" for fk in fks_qa)

    fks_audit = insp.get_foreign_keys("audit_logs")
    assert any(fk.get("referred_table") == "processing_state" for fk in fks_audit)
