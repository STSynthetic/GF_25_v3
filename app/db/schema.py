from __future__ import annotations

from sqlalchemy import (
    JSON,
    TIMESTAMP,
    CheckConstraint,
    ForeignKey,
    Index,
    MetaData,
    String,
    Table,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB

# Use naming convention for constraints to support alembic-friendly diffs later
metadata = MetaData(
    naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }
)

# Tables
from sqlalchemy import Column  # noqa: E402

tasks = Table(
    "tasks",
    metadata,
    Column("task_id", String(64), primary_key=True),
    Column("analysis_type", String(32), nullable=False),
    Column("status", String(32), nullable=False, index=True),
    Column("created_at", TIMESTAMP(timezone=True), nullable=False),
    Column("updated_at", TIMESTAMP(timezone=True), nullable=False),
    CheckConstraint("length(task_id) > 0", name="task_id_non_empty"),
)

processing_state = Table(
    "processing_state",
    metadata,
    Column("process_id", String(64), primary_key=True),
    Column(
        "task_id",
        String(64),
        ForeignKey("tasks.task_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
    Column("worker_id", String(64), nullable=False),
    Column("state", String(32), nullable=False),
    Column("started_at", TIMESTAMP(timezone=True), nullable=False),
    Column("finished_at", TIMESTAMP(timezone=True)),
)

qa_attempts = Table(
    "qa_attempts",
    metadata,
    Column("attempt_id", String(64), primary_key=True),
    Column(
        "task_id",
        String(64),
        ForeignKey("tasks.task_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
    Column("qa_stage", String(32), nullable=False),
    Column("validation_result", JSON().with_variant(JSONB, "postgresql"), nullable=False),
    Column("failure_reasons", JSON().with_variant(JSONB, "postgresql"), nullable=True),
    Column("corrective_prompt_used", Text(), nullable=True),
    Column("created_at", TIMESTAMP(timezone=True), nullable=False),
    Index("ix_qa_attempts_task_stage", "task_id", "qa_stage"),
)

audit_logs = Table(
    "audit_logs",
    metadata,
    Column("log_id", String(64), primary_key=True),
    Column(
        "process_id",
        String(64),
        ForeignKey("processing_state.process_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
    Column("event_type", String(64), nullable=False),
    Column("event_data", JSON().with_variant(JSONB, "postgresql"), nullable=True),
    Column("timestamp", TIMESTAMP(timezone=True), nullable=False),
)


def create_all(bind):
    """Create all tables on the given SQLAlchemy Engine or Connection."""
    metadata.create_all(bind)
