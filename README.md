# WhistleDrop

> A confidential, zero-knowledge reporting backend where individuals can submit anonymous reports and communicate with moderators without revealing their identity.

---

## Overview

**WhistleDrop** provides a privacy-first, zero-knowledge platform for anonymous report submission and tracking. Whistleblowers can submit sensitive reports and evidence without creating accounts or exposing personal identifiers. The backend enforces strict cryptographic separation, device metadata scrubbing, and forward-only status workflows designed to protect whistleblowers even in the event of internal database compromise.

### Core Principles & Architecture

- **Zero-Knowledge Case Codes ([ADR-0001](docs/adr/0001-hashed-case-codes.md))**:
  When a report is created, a cryptographically secure, human-friendly **Case Code** (format: `WD-XXXX-XXXX`) is generated and returned to the reporter exactly once. The database stores only the **Hashed Case Code** (SHA-256 digest). Subsequent status lookups hash the presented case code in-memory. Database possession alone does not grant access to individual report channels.
- **In-Memory Evidence Scrubbing**:
  Uploaded evidence files (JPEG, PNG, WebP up to 5 MB) undergo automatic in-memory EXIF, GPS, and device metadata removal via Pillow re-encoding prior to disk persistence.
- **Brute-Force Rate Limiting**:
  Status tracking endpoints employ sliding-window rate limiting to prevent case code guessing and enumeration attacks.
- **Data Minimization on Permanent Closure ([ADR-0002](docs/adr/0002-permanent-closure-data-minimization.md))**:
  Reports transition through a deterministic forward-only status workflow:
  `SUBMITTED` → `UNDER_REVIEW` → `RESOLVED` / `DISMISSED` → `PERMANENTLY_CLOSED`.
  Reaching `PERMANENTLY_CLOSED` irreversibly replaces descriptions with a standardized **Redaction Marker**, unlinks evidence files, and freezes dead drops.
- **Zero-Friction Developer Experience ([ADR-0003](docs/adr/0003-python-fastapi-stack.md))**:
  Built on Python 3.14, FastAPI, SQLAlchemy 2.0, and SQLite with full type safety, Pydantic v2 schemas, and interactive Swagger documentation (`/docs`). Managed with `uv`.

---

## Tech Stack

| Component | Technology | Rationale |
|-----------|------------|-----------|
| **Language** | Python 3.14+ | Modern language features and performance |
| **Framework** | FastAPI 0.115+ | Async performance, native OpenAPI docs, Pydantic v2 validation |
| **ORM / Storage** | SQLAlchemy 2.0 + SQLite | Zero-friction local development, zero container dependencies |
| **Image Processing** | Pillow (PIL) | In-memory EXIF/GPS scrubbing and sanitization |
| **Package Manager** | uv | Ultra-fast virtual environment and dependency resolution |
| **Testing** | pytest, pytest-asyncio, httpx | Async test runner and HTTP client |

---

## Getting Started

### Prerequisites

- [Python 3.14+](https://www.python.org/)
- [uv](https://docs.astral.sh/uv/) package manager

### Installation

Clone the repository and install dependencies with `uv`:

```bash
git clone https://github.com/libin-codes/whistle-drop.git
cd whistle-drop
uv sync
```

### Running the Application

Start the local development server with live reload:

```bash
uv run uvicorn app.main:app --reload
```

The service will be available at:
- **API Base URL**: `http://127.0.0.1:8000`
- **Interactive Swagger UI**: `http://127.0.0.1:8000/docs`
- **ReDoc Documentation**: `http://127.0.0.1:8000/redoc`

---

## API Endpoints

All primary endpoints are prefixed with `/api/v1`.

### 1. Submit an Anonymous Report
- **`POST /api/v1/reports`**
- **Request Body**:
  ```json
  {
    "category": "SECURITY",
    "description": "Observed unauthorized access credentials committed to public repositories.",
    "evidence_url": "/uploads/example.png"
  }
  ```
  _Allowed categories_: `SECURITY`, `HARASSMENT`, `CORRUPTION`, `TECHNICAL`, `OTHER` (case-insensitive).
- **Response** (`201 Created`):
  ```json
  {
    "case_code": "WD-ABCD-1234",
    "message": "Report submitted successfully."
  }
  ```
  > **Note**: The `case_code` is returned only once. It is never stored in plaintext.

### 2. Upload Evidence (Scrubbed)
- **`POST /api/v1/evidence/upload`**
- **Request**: `multipart/form-data` with `file` (JPEG, PNG, WebP up to 5 MB).
- **Behavior**: All EXIF/GPS metadata is scrubbed in-memory before saving with a UUID filename.
- **Response** (`201 Created`):
  ```json
  {
    "url": "/uploads/a1b2c3d4-e5f6-7890-abcd-ef1234567890.jpg",
    "message": "Evidence uploaded and metadata scrubbed."
  }
  ```

### 3. Track Report Status
- **`GET /api/v1/reports/track/{case_code}`**
- **Parameters**: `case_code` (e.g. `WD-ABCD-1234`)
- **Behavior**: Plaintext code is hashed in-memory to look up the record. Rate-limited to 10 requests / 60 seconds per client.
- **Response** (`200 OK`):
  ```json
  {
    "category": "SECURITY",
    "status": "SUBMITTED",
    "status_note": null,
    "created_at": "2026-10-06T20:00:00Z",
    "updated_at": "2026-10-06T20:00:00Z"
  }
  ```

### 4. Moderator Login
- **`POST /api/v1/auth/login`**
- **Request Body**:
  ```json
  {
    "username": "moderator",
    "password": "moderator123"
  }
  ```
  > **Note**: A default moderator account (`moderator` / `moderator123`) is auto-seeded on application startup.
- **Response** (`200 OK`):
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 86400
  }
  ```

### 5. List and Filter Reports (Moderator)
- **`GET /api/v1/moderator/reports`**
- **Headers**: `Authorization: Bearer <access_token>`
- **Query Parameters**:
  - `status` (optional): `SUBMITTED`, `UNDER_REVIEW`, `RESOLVED`, `DISMISSED`
  - `category` (optional): `SECURITY`, `HARASSMENT`, `CORRUPTION`, `TECHNICAL`, `OTHER`
  - `limit` (optional, default 50)
  - `offset` (optional, default 0)
- **Response** (`200 OK`):
  ```json
  [
    {
      "id": 1,
      "category": "SECURITY",
      "description": "Observed unauthorized access credentials committed to public repositories.",
      "evidence_url": "/uploads/example.png",
      "status": "SUBMITTED",
      "status_note": null,
      "created_at": "2026-10-06T20:00:00Z",
      "updated_at": "2026-10-06T20:00:00Z"
    }
  ]
  ```

### 6. Get Report Details (Moderator)
- **`GET /api/v1/moderator/reports/{report_id}`**
- **Headers**: `Authorization: Bearer <access_token>`
- **Response** (`200 OK`): Full report details (404 if not found).

### 7. Advance Report Status Workflow (Moderator)
- **`PATCH /api/v1/moderator/reports/{report_id}/status`**
- **Headers**: `Authorization: Bearer <access_token>`
- **Request Body**:
  ```json
  {
    "status": "UNDER_REVIEW",
    "status_update": "Assigned to primary investigator."
  }
  ```
  _Enforced transitions_:
  - `SUBMITTED` → `UNDER_REVIEW`, `DISMISSED`
  - `UNDER_REVIEW` → `RESOLVED`, `DISMISSED`
  Illegal transitions return `HTTP 400 Bad Request`.
- **Response** (`200 OK`): Updated report object.

### 8. Dead Drop Moderator Inquiry (Moderator)
- **`POST /api/v1/moderator/reports/{report_id}/messages`**
- **Headers**: `Authorization: Bearer <access_token>`
- **Request Body**:
  ```json
  {
    "content": "Can you specify the server IP address observed?"
  }
  ```
- **Response** (`201 Created`): Created message with `sender_role: "MODERATOR"`.

### 9. Dead Drop Whistleblower Reply (Reporter)
- **`POST /api/v1/reports/track/{case_code}/messages`**
- **Request Body**:
  ```json
  {
    "content": "The backend payment gateway auth cluster."
  }
  ```
- **Response** (`201 Created`): Created message with `sender_role: "REPORTER"`.

### 10. Permanent Case Closure (Moderator)
- **`POST /api/v1/moderator/reports/{report_id}/close`**
- **Headers**: `Authorization: Bearer <access_token>`
- **Request Body** (optional):
  ```json
  {
    "status_note": "Case permanently archived after forensic review."
  }
  ```
- **Behavior (ADR-0002)**:
  - Irreversibly sets status to `PERMANENTLY_CLOSED`.
  - Overwrites description with standardized Redaction Marker (`[REDACTED - CASE PERMANENTLY CLOSED]`).
  - Shreds and unlinks any attached evidence file from local storage.
  - Freezes the Dead Drop message thread against subsequent writes.
  - Rejects further status updates, closures, or messages with `HTTP 400 Bad Request`.
- **Response** (`200 OK`): Redacted report object.

---

## Running Tests

Run the test suite using `pytest`:

```bash
uv run pytest
```

The test suite covers:
- Cryptographic generation and SHA-256 hashing of case codes
- Report submission and validation (category normalization, rejection of blank descriptions)
- Image upload validation and in-memory EXIF metadata stripping
- Zero-knowledge status tracking and sliding-window rate limiting
- Moderator auto-seeding, JWT authentication, and Bearer token enforcement
- Filtered report review with category/status filters and pagination
- Forward-only Status Workflow transitions and illegal jump rejection
- Two-way confidential Dead Drop messaging between moderators and whistleblowers
- Permanent case closure data minimization, description redaction, file shredding, and closure immutability

---

## Domain Language & Documentation

WhistleDrop enforces a strict ubiquitous domain language. Refer to the canonical documentation:

- [GLOSSARY.md](GLOSSARY.md): Canonical domain terms and vocabulary rules.
- [docs/adr/](docs/adr/): Architecture Decision Records
  - [ADR-0001: Hashed Case Codes for Zero-Knowledge Tracking](docs/adr/0001-hashed-case-codes.md)
  - [ADR-0002: Data Minimization on Permanent Case Closure](docs/adr/0002-permanent-closure-data-minimization.md)
  - [ADR-0003: Python, FastAPI, and SQLite for Backend Stack](docs/adr/0003-python-fastapi-stack.md)

---

## License

MIT
