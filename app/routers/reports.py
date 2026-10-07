"""Whistleblower report submission and tracking routes."""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.case_codes import generate_case_code, hash_case_code
from app.database import get_db
from app.models import CategoryEnum, Report
from app.rate_limit import tracking_limiter
from app.schemas import ReportCreate, ReportCreated, ReportStatus

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("", response_model=ReportCreated, status_code=201)
@router.post("/", response_model=ReportCreated, status_code=201, include_in_schema=False)
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


@router.get("/track/{case_code}", response_model=ReportStatus)
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

    return ReportStatus.from_report(report)
