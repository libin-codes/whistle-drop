# WhistleDrop

A confidential, zero-knowledge reporting backend where individuals can submit anonymous reports and communicate with moderators without revealing their identity.

## Language

**Report**:
An anonymous submission containing an issue category, detailed description, and optional evidence.
_Avoid_: Ticket, complaint, issue, casefile

**Case Code**:
The cryptographically random, human-friendly secret token returned to the reporter upon submission to track progress.
_Avoid_: Tracking number, reference ID, ticket ID

**Hashed Case Code**:
The SHA-256 digest of the case code stored in the database for zero-knowledge lookup.
_Avoid_: Password, salt

**Dead Drop**:
The anonymous, asynchronous message thread attached to a report allowing bi-directional communication between moderators and the reporter without authentication accounts.
_Avoid_: Chat, comment section, mailbox

**Moderator**:
An authenticated user authorized to inspect, triage, communicate on, and update the status of reports.
_Avoid_: Admin, agent, reviewer

**Status Workflow**:
The deterministic forward-only lifecycle of a report (`SUBMITTED` → `UNDER_REVIEW` → `RESOLVED` / `DISMISSED` → `PERMANENTLY_CLOSED`).
_Avoid_: Pipeline, issue state

**Permanent Closure**:
The irreversible terminal state of a report that triggers data minimization and permanently forbids further state changes or messages.
_Avoid_: Soft delete, archive

**Evidence Scrubbing**:
In-memory removal of device metadata (EXIF, GPS, camera details) from uploaded files before persistence.
_Avoid_: File compression, cleaning

**Redaction Marker**:
The standardized tombstone text replacing the description of a permanently closed case to enforce data minimization.
_Avoid_: Deletion flag, placeholder

