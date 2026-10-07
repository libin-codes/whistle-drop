"""Pydantic request/response schemas for the WhistleDrop API."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class CategoryIn(str, Enum):
    SECURITY = "SECURITY"
    HARASSMENT = "HARASSMENT"
    CORRUPTION = "CORRUPTION"
    TECHNICAL = "TECHNICAL"
    OTHER = "OTHER"


class ReportCreate(BaseModel):
    category: CategoryIn
    description: str = Field(min_length=1)
    evidence_url: str | None = None

    @field_validator("category", mode="before")
    @classmethod
    def normalize_category(cls, v: Any) -> Any:
        if isinstance(v, str):
            return v.upper()
        return v

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Description cannot be blank.")
        return v


class ReportCreated(BaseModel):
    case_code: str = Field(
        description="Plaintext case code — returned once, never stored."
    )
    message: str = "Report submitted successfully."


class ReportStatus(BaseModel):
    """Public tracking response — no internal IDs exposed."""

    category: str
    status: str
    status_note: str | None = None
    status_update: str | None = None
    created_at: datetime
    updated_at: datetime


class EvidenceUploaded(BaseModel):
    url: str
    message: str = "Evidence uploaded and metadata scrubbed."


class ErrorDetail(BaseModel):
    detail: str


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 86400


class ModeratorReportResponse(BaseModel):
    """Report representation for authorized moderators — no reporter identifiers."""

    id: int
    category: str
    description: str
    evidence_url: str | None = None
    status: str
    status_note: str | None = None
    status_update: str | None = None
    created_at: datetime
    updated_at: datetime


class ReportStatusUpdate(BaseModel):
    status: str
    status_update: str | None = None
    status_note: str | None = None
