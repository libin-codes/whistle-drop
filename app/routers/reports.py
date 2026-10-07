"""Whistleblower report submission and tracking routes."""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.case_codes import generate_case_code, hash_case_code
from app.database import get_db
from app.models import (
    CategoryEnum,
    Report,
    ReportMessage,
    SenderRoleEnum,
    StatusEnum,
)
from app.rate_limit import tracking_limiter
from app.schemas import (
    MessageCreate,
    MessageResponse,
    ReportCreate,
    ReportCreated,
    ReportStatus,
)

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


@router.post("/track/{case_code}/messages", response_model=MessageResponse, status_code=201)
@router.post("/track/{case_code}/messages/", response_model=MessageResponse, status_code=201, include_in_schema=False)
def post_reporter_message(
    case_code: str,
    payload: MessageCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    """Post an anonymous reply to the Dead Drop thread authenticated solely by Case Code."""
    tracking_limiter.check(request)

    hashed = hash_case_code(case_code)
    report = db.query(Report).filter(Report.hashed_case_code == hashed).first()

    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")

    if report.status == StatusEnum.PERMANENTLY_CLOSED:
        raise HTTPException(
            status_code=400,
            detail="Cannot send messages on a permanently closed report.",
        )

    msg = ReportMessage(
        report_id=report.id,
        sender_role=SenderRoleEnum.REPORTER,
        content=payload.content,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)

    return MessageResponse.from_message(msg)


@router.get("/track/{case_code}/messages", response_model=list[MessageResponse])
@router.get("/track/{case_code}/messages/", response_model=list[MessageResponse], include_in_schema=False)
def get_reporter_messages(
    case_code: str,
    request: Request,
    db: Session = Depends(get_db),
):
    """Get the Dead Drop message thread for a report using the Case Code."""
    tracking_limiter.check(request)

    hashed = hash_case_code(case_code)
    report = db.query(Report).filter(Report.hashed_case_code == hashed).first()

    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")

    return [MessageResponse.from_message(m) for m in (report.messages or [])]

