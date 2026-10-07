"""API routes for whistleblower report submission, evidence upload, and tracking."""

import os
import uuid
from io import BytesIO
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile
from PIL import Image
from sqlalchemy.orm import Session

from app.auth import create_access_token, get_current_moderator, verify_password
from app.case_codes import generate_case_code, hash_case_code
from app.database import get_db
from app.models import CategoryEnum, Moderator, Report, StatusEnum
from app.rate_limit import tracking_limiter
from app.schemas import (
    EvidenceUploaded,
    LoginRequest,
    ModeratorReportResponse,
    ReportCreate,
    ReportCreated,
    ReportStatus,
    ReportStatusUpdate,
    TokenResponse,
)

router = APIRouter(prefix="/api/v1")

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


@router.post("/reports", response_model=ReportCreated, status_code=201)
def create_report(payload: ReportCreate, db: Session = Depends(get_db)):
    """Submit an anonymous report.

    Returns the plaintext Case Code exactly once — it is never stored.
    """
    case_code = generate_case_code()
    hashed = hash_case_code(case_code)

    report = Report(
        hashed_case_code=hashed,
        category=CategoryEnum(payload.category.value),
        description=payload.description,
        evidence_url=payload.evidence_url,
    )
    db.add(report)
    db.commit()

    return ReportCreated(case_code=case_code)


@router.post("/evidence/upload", response_model=EvidenceUploaded, status_code=201)
async def upload_evidence(file: UploadFile):
    """Upload an image file with automatic EXIF/GPS metadata stripping.

    Accepts JPEG, PNG, and WebP up to 5 MB.
    """
    # Validate content type
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type '{file.content_type}'. "
            f"Allowed: JPEG, PNG, WebP.",
        )

    # Read and validate size
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds maximum size of {MAX_FILE_SIZE // (1024 * 1024)} MB.",
        )

    # Strip EXIF metadata in-memory by re-encoding through Pillow
    try:
        image = Image.open(BytesIO(contents))
        image.load()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid image file.")

    img_format = image.format or "PNG"
    save_image: Image.Image = image
    if img_format == "JPEG" and image.mode in ("RGBA", "LA", "P"):
        save_image = image.convert("RGB")

    # Create a clean image without metadata
    clean_buffer = BytesIO()
    save_image.save(clean_buffer, format=img_format)
    clean_data = clean_buffer.getvalue()

    # Save with UUID filename
    ext = {"JPEG": ".jpg", "PNG": ".png", "WEBP": ".webp"}.get(img_format, ".png")
    filename = f"{uuid.uuid4()}{ext}"
    filepath = UPLOAD_DIR / filename
    filepath.write_bytes(clean_data)

    url = f"/uploads/{filename}"
    return EvidenceUploaded(url=url)


@router.get("/reports/track/{case_code}", response_model=ReportStatus)
def track_report(
    case_code: str,
    request: Request,
    db: Session = Depends(get_db),
):
    """Look up a report's current status using the plaintext Case Code.

    The code is hashed in-memory for zero-knowledge database lookup (ADR-0001).
    Rate-limited to prevent brute-force enumeration.
    """
    tracking_limiter.check(request)

    hashed = hash_case_code(case_code)
    report = db.query(Report).filter(Report.hashed_case_code == hashed).first()

    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")

    return ReportStatus(
        category=report.category.value,
        status=report.status.value,
        status_note=report.status_note,
        status_update=report.status_note,
        created_at=report.created_at,
        updated_at=report.updated_at,
    )


@router.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate moderator and return a 24-hour HS256 JWT access token."""
    moderator = (
        db.query(Moderator)
        .filter(Moderator.username == payload.username)
        .first()
    )
    if not moderator or not verify_password(payload.password, moderator.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": moderator.username, "role": "MODERATOR"}
    )
    return TokenResponse(access_token=access_token, token_type="bearer", expires_in=86400)


ALLOWED_STATUS_TRANSITIONS: dict[StatusEnum, set[StatusEnum]] = {
    StatusEnum.SUBMITTED: {StatusEnum.UNDER_REVIEW, StatusEnum.DISMISSED},
    StatusEnum.UNDER_REVIEW: {StatusEnum.RESOLVED, StatusEnum.DISMISSED},
    StatusEnum.RESOLVED: set(),
    StatusEnum.DISMISSED: set(),
    StatusEnum.PERMANENTLY_CLOSED: set(),
}


def _to_moderator_report_response(report: Report) -> ModeratorReportResponse:
    """Format a Report entity into a ModeratorReportResponse."""
    return ModeratorReportResponse(
        id=report.id,
        category=report.category.value,
        description=report.description,
        evidence_url=report.evidence_url,
        status=report.status.value,
        status_note=report.status_note,
        status_update=report.status_note,
        created_at=report.created_at,
        updated_at=report.updated_at,
    )


@router.get("/moderator/reports", response_model=list[ModeratorReportResponse])
def list_reports(
    status: str | None = Query(default=None),
    category: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_moderator: Moderator = Depends(get_current_moderator),
    db: Session = Depends(get_db),
):
    """List reports with optional category and status filtering and pagination.

    Moderators cannot see any reporter IP or identifying metadata.
    """
    query = db.query(Report)

    if category:
        cat_upper = category.strip().upper()
        if cat_upper in CategoryEnum.__members__:
            query = query.filter(Report.category == CategoryEnum[cat_upper])
        else:
            return []

    if status:
        st_upper = status.strip().upper()
        if st_upper in StatusEnum.__members__:
            query = query.filter(Report.status == StatusEnum[st_upper])
        else:
            return []

    reports = (
        query.order_by(Report.created_at.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return [_to_moderator_report_response(r) for r in reports]


@router.get("/moderator/reports/{report_id}", response_model=ModeratorReportResponse)
def get_report_detail(
    report_id: int,
    current_moderator: Moderator = Depends(get_current_moderator),
    db: Session = Depends(get_db),
):
    """Retrieve full details for a single report. Returns 404 if not found."""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")

    return _to_moderator_report_response(report)


@router.patch(
    "/moderator/reports/{report_id}/status",
    response_model=ModeratorReportResponse,
)
def update_report_status(
    report_id: int,
    payload: ReportStatusUpdate,
    current_moderator: Moderator = Depends(get_current_moderator),
    db: Session = Depends(get_db),
):
    """Advance report status through the Status Workflow state machine.

    Enforces valid forward transitions and rejects illegal jumps with HTTP 400.
    Optionally sets a status_update note readable by the whistleblower.
    """
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")

    target_status_name = payload.status.strip().upper()
    if target_status_name not in StatusEnum.__members__:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid target status '{payload.status}'.",
        )

    target_status = StatusEnum[target_status_name]
    allowed_next = ALLOWED_STATUS_TRANSITIONS.get(report.status, set())
    if target_status not in allowed_next:
        raise HTTPException(
            status_code=400,
            detail=f"Illegal status transition from {report.status.value} to {target_status.value}.",
        )

    report.status = target_status
    if payload.status_update is not None:
        report.status_note = payload.status_update
    elif payload.status_note is not None:
        report.status_note = payload.status_note

    db.commit()
    db.refresh(report)

    return _to_moderator_report_response(report)

