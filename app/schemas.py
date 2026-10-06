"""Pydantic request/response schemas for the WhistleDrop API."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


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


class ReportCreated(BaseModel):
    case_code: str = Field(
        description="Plaintext case code — returned once, never stored."
    )
    message: str = "Report submitted successfully."


class ReportStatus(BaseModel):
    """Public tracking response — no internal IDs exposed."""

    category: str
    status: str
    created_at: datetime
    updated_at: datetime


class EvidenceUploaded(BaseModel):
    url: str
    message: str = "Evidence uploaded and metadata scrubbed."


class ErrorDetail(BaseModel):
    detail: str
