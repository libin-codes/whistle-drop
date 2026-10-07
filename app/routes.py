"""API routes aggregation for WhistleDrop.

Combines modular routers for authentication, evidence, reports, and moderation
under the /api/v1 prefix.
"""

from pathlib import Path

from fastapi import APIRouter

import app.evidence as evidence
from app.routers.auth import router as auth_router
from app.routers.evidence import router as evidence_router
from app.routers.moderator import router as moderator_router
from app.routers.reports import router as reports_router
from app.workflow import ALLOWED_STATUS_TRANSITIONS, REDACTION_MARKER

# Expose UPLOAD_DIR for backward compatibility with existing tests and fixtures
UPLOAD_DIR: Path = evidence.UPLOAD_DIR

router = APIRouter(prefix="/api/v1")
router.include_router(reports_router)
router.include_router(evidence_router)
router.include_router(auth_router)
router.include_router(moderator_router)

__all__ = ["router", "UPLOAD_DIR", "ALLOWED_STATUS_TRANSITIONS", "REDACTION_MARKER"]
