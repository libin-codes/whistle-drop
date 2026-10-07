"""SQLAlchemy ORM models for the WhistleDrop domain."""

import enum

from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class CategoryEnum(enum.Enum):
    SECURITY = "SECURITY"
    HARASSMENT = "HARASSMENT"
    CORRUPTION = "CORRUPTION"
    TECHNICAL = "TECHNICAL"
    OTHER = "OTHER"


class StatusEnum(enum.Enum):
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    RESOLVED = "RESOLVED"
    DISMISSED = "DISMISSED"
    PERMANENTLY_CLOSED = "PERMANENTLY_CLOSED"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Report(Base):
    """A whistleblower report. Only the hashed case code is stored (ADR-0001)."""

    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    hashed_case_code: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )
    category: Mapped[CategoryEnum] = mapped_column(
        Enum(CategoryEnum), nullable=False
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    status: Mapped[StatusEnum] = mapped_column(
        Enum(StatusEnum), nullable=False, default=StatusEnum.SUBMITTED
    )
    status_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )


class Moderator(Base):
    """An authenticated moderator authorized to triage and update reports."""

    __tablename__ = "moderators"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )
    hashed_password: Mapped[str] = mapped_column(String(256), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )

