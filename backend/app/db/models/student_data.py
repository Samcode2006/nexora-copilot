"""Student-owned records introduced by the Phase 1 schema migration."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    Text,
    UniqueConstraint,
    Uuid,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ProfileConsent(Base):
    __tablename__ = "profile_consents"
    __table_args__ = (
        CheckConstraint(
            "consent_type = 'resume_processing'", name="ck_profile_consents_supported_type"
        ),
        CheckConstraint(
            "withdrawn_at IS NULL OR granted_at IS NOT NULL",
            name="ck_profile_consents_withdrawal_requires_grant",
        ),
    )

    student_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("auth.users.id", ondelete="CASCADE"), primary_key=True
    )
    consent_type: Mapped[str] = mapped_column(Text, primary_key=True)
    granted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    withdrawn_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Resume(Base):
    __tablename__ = "resumes"
    __table_args__ = (
        UniqueConstraint("id", "student_id", name="uq_resumes_id_student"),
        CheckConstraint("length(filename) BETWEEN 1 AND 255", name="ck_resumes_filename_length"),
        CheckConstraint(
            "content_type IN ('application/pdf', "
            "'application/vnd.openxmlformats-officedocument.wordprocessingml.document')",
            name="ck_resumes_content_type",
        ),
        CheckConstraint("size_bytes BETWEEN 1 AND 5242880", name="ck_resumes_size_bytes"),
        Index("ix_resumes_student_created", "student_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    student_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("auth.users.id", ondelete="CASCADE"), nullable=False
    )
    filename: Mapped[str] = mapped_column(Text, nullable=False)
    content_type: Mapped[str] = mapped_column(Text, nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ProfileFact(Base):
    __tablename__ = "profile_facts"
    __table_args__ = (
        UniqueConstraint("id", "student_id", name="uq_profile_facts_id_student"),
        CheckConstraint(
            "fact_type IN ('education','skill','project','experience','achievement','certification')",
            name="ck_profile_facts_type",
        ),
        CheckConstraint(
            "status IN ('pending_confirmation','confirmed','archived')",
            name="ck_profile_facts_status",
        ),
        CheckConstraint("source IN ('student','resume')", name="ck_profile_facts_source"),
        CheckConstraint("revision >= 1", name="ck_profile_facts_revision"),
        CheckConstraint("jsonb_typeof(data) = 'object'", name="ck_profile_facts_data_object"),
        CheckConstraint(
            "confidence IS NULL OR confidence IN ('high','medium','low')",
            name="ck_profile_facts_confidence",
        ),
        CheckConstraint(
            "(status = 'archived') = (archived_at IS NOT NULL)",
            name="ck_profile_facts_archive_timestamp",
        ),
        CheckConstraint(
            "source <> 'resume' OR (confidence IS NOT NULL AND source_ref IS NOT NULL)",
            name="ck_profile_facts_resume_provenance",
        ),
        Index("ix_profile_facts_student_status_type", "student_id", "status", "fact_type"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    student_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("auth.users.id", ondelete="CASCADE"), nullable=False
    )
    fact_type: Mapped[str] = mapped_column(Text, nullable=False)
    data: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(Text, nullable=False)
    revision: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    ever_cited: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    confidence: Mapped[str | None] = mapped_column(Text)
    source_ref: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ProfileFactRevision(Base):
    __tablename__ = "profile_fact_revisions"
    __table_args__ = (
        UniqueConstraint(
            "fact_id", "revision", "student_id", name="uq_profile_fact_revisions_fact_rev_student"
        ),
        ForeignKeyConstraint(
            ["fact_id", "student_id"],
            ["profile_facts.id", "profile_facts.student_id"],
            ondelete="CASCADE",
            name="fk_profile_fact_revisions_fact_student",
        ),
        ForeignKeyConstraint(
            ["student_id"],
            ["auth.users.id"],
            ondelete="NO ACTION",
            name="fk_profile_fact_revisions_user",
        ),
        CheckConstraint("revision >= 1", name="ck_profile_fact_revisions_revision"),
        CheckConstraint(
            "jsonb_typeof(data) = 'object'", name="ck_profile_fact_revisions_data_object"
        ),
        Index("ix_profile_fact_revisions_student_created", "student_id", "created_at"),
    )

    fact_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    revision: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    data: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Task(Base):
    __tablename__ = "tasks"
    __table_args__ = (
        UniqueConstraint("id", "student_id", name="uq_tasks_id_student"),
        ForeignKeyConstraint(
            ["retry_of", "student_id"],
            ["tasks.id", "tasks.student_id"],
            ondelete="CASCADE",
            name="fk_tasks_retry_same_student",
        ),
        CheckConstraint(
            "kind IN ('resume_parse','job_refresh','document_generation','evidence_validation',"
            "'question_generation','answer_evaluation')",
            name="ck_tasks_kind",
        ),
        CheckConstraint("status IN ('queued','running','succeeded','failed')", name="ck_tasks_status"),
        CheckConstraint("trigger IN ('explicit','automatic')", name="ck_tasks_trigger"),
        CheckConstraint("attempt >= 1", name="ck_tasks_attempt"),
        CheckConstraint(
            "(attempt = 1 AND retry_of IS NULL) OR (attempt > 1 AND retry_of IS NOT NULL)",
            name="ck_tasks_retry_shape",
        ),
        CheckConstraint("timeout_seconds > 0", name="ck_tasks_timeout_seconds"),
        CheckConstraint(
            "(status IN ('queued','running','succeeded') AND error_code IS NULL AND retryable IS NULL) OR "
            "(status = 'failed' AND error_code IS NOT NULL AND retryable IS NOT NULL)",
            name="ck_tasks_error_state",
        ),
        CheckConstraint(
            "(status = 'queued' AND started_at IS NULL AND finished_at IS NULL) OR "
            "(status = 'running' AND started_at IS NOT NULL AND finished_at IS NULL) OR "
            "(status = 'succeeded' AND finished_at IS NOT NULL AND started_at IS NOT NULL) OR "
            "(status = 'failed' AND finished_at IS NOT NULL)",
            name="ck_tasks_timestamps",
        ),
        Index("ix_tasks_student_kind_trigger_created", "student_id", "kind", "trigger", "created_at"),
        Index(
            "uq_tasks_one_live_resource",
            "student_id",
            "kind",
            "resource_type",
            "resource_id",
            unique=True,
            postgresql_where=text("status IN ('queued','running')"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    student_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("auth.users.id", ondelete="CASCADE"), nullable=False
    )
    kind: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="queued")
    trigger: Mapped[str] = mapped_column(Text, nullable=False, server_default="explicit")
    retry_of: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    attempt: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    error_code: Mapped[str | None] = mapped_column(Text)
    retryable: Mapped[bool | None] = mapped_column(Boolean)
    resource_type: Mapped[str] = mapped_column(Text, nullable=False)
    resource_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    timeout_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
