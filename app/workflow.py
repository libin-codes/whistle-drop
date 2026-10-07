"""Status Workflow state machine definitions and transition validation."""

from app.models import StatusEnum

ALLOWED_STATUS_TRANSITIONS: dict[StatusEnum, set[StatusEnum]] = {
    StatusEnum.SUBMITTED: {StatusEnum.UNDER_REVIEW, StatusEnum.DISMISSED},
    StatusEnum.UNDER_REVIEW: {StatusEnum.RESOLVED, StatusEnum.DISMISSED},
    StatusEnum.RESOLVED: set(),
    StatusEnum.DISMISSED: set(),
    StatusEnum.PERMANENTLY_CLOSED: set(),
}


def can_transition(current_status: StatusEnum, target_status: StatusEnum) -> bool:
    """Check whether a transition between two statuses is permitted in the workflow."""
    return target_status in ALLOWED_STATUS_TRANSITIONS.get(current_status, set())
