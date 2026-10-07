"""Moderator portal routes for listing, inspecting, and updating reports."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.auth import get_current_moderator
from app.database import get_db
from app.models import CategoryEnum, Moderator, Report, StatusEnum
from app.schemas import ModeratorReportResponse, ReportStatusUpdate
from app.workflow import can_transition

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
