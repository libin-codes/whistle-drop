from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.auth import get_current_moderator
from app.database import get_db
from app.evidence import delete_evidence
from app.models import (
    CategoryEnum,
    Moderator,
    Report,
    ReportMessage,
    SenderRoleEnum,
    StatusEnum,
)
from app.schemas import (
    CaseCloseRequest,
    MessageCreate,
    MessageResponse,
    ModeratorReportResponse,
    ReportStatusUpdate,
)
from app.workflow import REDACTION_MARKER, can_transition

router = APIRouter(prefix="/moderator/reports", tags=["moderator"])


@router.get("", response_model=list[ModeratorReportResponse])
@router.get("/", response_model=list[ModeratorReportResponse], include_in_schema=False)
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

    return [ModeratorReportResponse.from_report(r) for r in reports]


@router.get("/{report_id}", response_model=ModeratorReportResponse)
def get_report_detail(
    report_id: int,
    current_moderator: Moderator = Depends(get_current_moderator),
    db: Session = Depends(get_db),
):
    """Retrieve full details for a single report. Returns 404 if not found."""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")

    return ModeratorReportResponse.from_report(report)


@router.patch("/{report_id}/status", response_model=ModeratorReportResponse)
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

    if report.status == StatusEnum.PERMANENTLY_CLOSED:
        raise HTTPException(
            status_code=400,
            detail="Permanently closed reports cannot be modified.",
        )

    target_status_name = payload.status.strip().upper()
    if target_status_name not in StatusEnum.__members__:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid target status '{payload.status}'.",
        )

    target_status = StatusEnum[target_status_name]
    if not can_transition(report.status, target_status):
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

    return ModeratorReportResponse.from_report(report)


@router.post("/{report_id}/messages", response_model=MessageResponse, status_code=201)
@router.post("/{report_id}/messages/", response_model=MessageResponse, status_code=201, include_in_schema=False)
def post_moderator_message(
    report_id: int,
    payload: MessageCreate,
    current_moderator: Moderator = Depends(get_current_moderator),
    db: Session = Depends(get_db),
):
    """Post an authenticated moderator inquiry or note to the report's Dead Drop thread."""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")

    if report.status == StatusEnum.PERMANENTLY_CLOSED:
        raise HTTPException(
            status_code=400,
            detail="Cannot send messages on a permanently closed report.",
        )

    msg = ReportMessage(
        report_id=report.id,
        sender_role=SenderRoleEnum.MODERATOR,
        content=payload.content,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)

    return MessageResponse.from_message(msg)


@router.get("/{report_id}/messages", response_model=list[MessageResponse])
@router.get("/{report_id}/messages/", response_model=list[MessageResponse], include_in_schema=False)
def get_moderator_messages(
    report_id: int,
    current_moderator: Moderator = Depends(get_current_moderator),
    db: Session = Depends(get_db),
):
    """Get the Dead Drop message thread for a report."""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")

    return [MessageResponse.from_message(m) for m in (report.messages or [])]


@router.post("/{report_id}/close", response_model=ModeratorReportResponse)
@router.post("/{report_id}/close/", response_model=ModeratorReportResponse, include_in_schema=False)
def close_report(
    report_id: int,
    payload: CaseCloseRequest | None = Body(default=None),
    current_moderator: Moderator = Depends(get_current_moderator),
    db: Session = Depends(get_db),
):
    """Irreversibly close a report and trigger permanent case closure data minimization (ADR-0002).

    - Transitions status to PERMANENTLY_CLOSED
    - Overwrites description with standardized Redaction Marker
    - Unlinks and shreds attached local evidence files from disk
    - Freezes the Dead Drop message thread against subsequent writes
    """
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")

    if report.status == StatusEnum.PERMANENTLY_CLOSED:
        raise HTTPException(
            status_code=400,
            detail="Report is already permanently closed.",
        )

    # Transition status
    report.status = StatusEnum.PERMANENTLY_CLOSED

    # Overwrite description with standardized Redaction Marker
    report.description = REDACTION_MARKER

    # Shred local evidence file from disk storage
    if report.evidence_url:
        delete_evidence(report.evidence_url)
        report.evidence_url = None

    # Apply optional status note / update if provided
    if payload:
        note = payload.status_update or payload.status_note or payload.reason
        if note:
            report.status_note = note

    db.commit()
    db.refresh(report)

    return ModeratorReportResponse.from_report(report)

