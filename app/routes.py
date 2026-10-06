"""API routes for whistleblower report submission, evidence upload, and tracking."""

import os
import uuid
from io import BytesIO
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile
from PIL import Image
from sqlalchemy.orm import Session

from app.case_codes import generate_case_code, hash_case_code
from app.database import get_db
from app.models import CategoryEnum, Report
from app.rate_limit import tracking_limiter
from app.schemas import EvidenceUploaded, ReportCreate, ReportCreated, ReportStatus

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
    if img_format == "JPEG" and image.mode in ("RGBA", "LA", "P"):
        image = image.convert("RGB")

    # Create a clean image without metadata
    clean_buffer = BytesIO()
    image.save(clean_buffer, format=img_format)
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
        created_at=report.created_at,
        updated_at=report.updated_at,
    )
