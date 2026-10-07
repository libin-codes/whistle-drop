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
- **Embedded Dashboard**:
  A responsive, dark-mode single-page dashboard served at `GET /` with zero external frontend dependencies. Whistleblowers can submit reports, copy case codes, and track cases. Moderators can log in, triage reports, advance status, and communicate via the Dead Drop.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        WhistleDrop                              │
│                                                                 │
│  ┌──────────┐  ┌──────────────────────────────────────────────┐ │
│  │ Dashboard │  │             FastAPI Application              │ │
│  │  GET /    │  │                                              │ │
│  │(Embedded) │  │  ┌─────────┐  ┌───────────┐  ┌───────────┐ │ │
│  └──────────┘  │  │ Reports  │  │ Evidence  │  │   Auth    │ │ │
│                │  │ Router   │  │  Router   │  │  Router   │ │ │
│  ┌──────────┐  │  └────┬─────┘  └─────┬─────┘  └─────┬─────┘ │ │
│  │ Swagger  │  │       │              │              │       │ │
│  │ GET /docs│  │  ┌────┴──────────────┴──────────────┴─────┐ │ │
│  └──────────┘  │  │           Moderator Router             │ │ │
│                │  └────────────────────┬───────────────────┘ │ │
│                │                       │                     │ │
│                │  ┌────────────────────┴───────────────────┐ │ │
│                │  │        Core Services Layer             │ │ │
│                │  │  case_codes │ workflow │ rate_limit     │ │ │
│                │  │  evidence   │ auth     │ database       │ │ │
│                │  └────────────────────┬───────────────────┘ │ │
│                │                       │                     │ │
│                │  ┌────────────────────┴───────────────────┐ │ │
│                │  │     SQLite (whistledrop.db)            │ │ │
│                │  │  ┌──────────┬──────────────┬─────────┐ │ │ │
│                │  │  │ reports  │report_messages│moderators│ │ │ │
│                │  │  └──────────┴──────────────┴─────────┘ │ │ │
│                │  └────────────────────────────────────────┘ │ │
│                └──────────────────────────────────────────────┘ │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │            /uploads/ (Static File Serving)                │   │
│  │            UUID-named, EXIF-scrubbed evidence files        │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Threat Model & Anonymity Proofs

### Threat: Database Compromise

**Mitigation**: Zero-knowledge case codes ([ADR-0001](docs/adr/0001-hashed-case-codes.md)). The plaintext Case Code (`WD-XXXX-XXXX`) is returned to the reporter exactly once and never persisted. The database stores only the irreversible SHA-256 digest. An attacker with full database access cannot reconstruct case codes to access report channels.

**Proof**: Given SHA-256's preimage resistance (2^256 search space), and case codes drawn from a 36-character alphanumeric alphabet (8 random characters = ~41 bits of entropy), brute-force enumeration is throttled to 10 attempts per 60 seconds per IP. Exhausting the space at maximum rate would take ~7,000 years.

### Threat: Device Metadata Leakage

**Mitigation**: In-memory evidence scrubbing. All uploaded images are decoded and re-encoded via Pillow before persistence, stripping EXIF, GPS coordinates, camera make/model, software version, and all other metadata tags. Only raw pixel data survives.

### Threat: Post-Resolution Data Exposure

**Mitigation**: Permanent closure with data minimization ([ADR-0002](docs/adr/0002-permanent-closure-data-minimization.md)). Upon permanent closure:
1. Report description is overwritten with `[REDACTED - CASE PERMANENTLY CLOSED]`
2. Evidence files are physically deleted from disk (not just unlinked)
3. The Dead Drop thread is frozen against new writes
4. All subsequent modifications are rejected with HTTP 400

### Threat: Brute-Force Case Code Enumeration

**Mitigation**: Sliding-window rate limiter on all tracking endpoints. 10 requests per 60-second window per client IP. Exceeding the limit returns HTTP 429.

### Threat: Unauthorized Moderator Access

**Mitigation**: HS256 JWT authentication with PBKDF2-HMAC-SHA256 (100,000 iterations) password hashing. All moderator endpoints require a valid Bearer token. Tokens expire after 24 hours.

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
| **Containerization** | Docker + Docker Compose | One-command deployment alternative |

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
- **Dashboard**: `http://127.0.0.1:8000` — embedded web UI
- **Interactive Swagger UI**: `http://127.0.0.1:8000/docs`
- **ReDoc Documentation**: `http://127.0.0.1:8000/redoc`

### Running with Docker

Build and run with a single command:

```bash
docker compose up --build
```

Or with custom credentials:

```bash
JWT_SECRET_KEY=my-production-secret \
MODERATOR_USERNAME=admin \
MODERATOR_PASSWORD=secure-password-here \
docker compose up --build
```

The application will be available at `http://localhost:8000`.

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `JWT_SECRET_KEY` | `whistledrop-jwt-moderator-secret-key-32b` | Secret key for HS256 JWT signing |
| `MODERATOR_USERNAME` | `moderator` | Default moderator account username |
| `MODERATOR_PASSWORD` | `moderator123` | Default moderator account password |

---

## Embedded Dashboard

The dashboard at `GET /` provides three functional tabs:

### 🔒 Whistleblower Submit
Submit an anonymous report with category selection, description, and optional image evidence upload. The generated Case Code is displayed with a copy-to-clipboard button and a warning that it is shown only once.

### 🔍 Whistleblower Track
Enter a Case Code to view the report's current status (color-coded badge), moderator update notes, and the full Dead Drop message thread. Post anonymous replies directly from the interface.

### 🛡️ Moderator Portal
Log in with credentials to access the full moderation interface: list and filter reports, view details, transition statuses through the workflow, post Dead Drop messages, and trigger permanent case closure with confirmation.

---

## API Endpoints

All primary endpoints are prefixed with `/api/v1`. Interactive documentation with full schemas is available at `/docs`.

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
    "messages": [],
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
      "messages": [],
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

## Example cURL Requests

### Submit a Report

```bash
curl -X POST http://localhost:8000/api/v1/reports \
  -H "Content-Type: application/json" \
  -d '{
    "category": "CORRUPTION",
    "description": "Observed unusual fund transfers in Q3 treasury reports."
  }'
```

**Response:**
```json
{
  "case_code": "WD-K7M2-X9PL",
  "message": "Report submitted successfully."
}
```

### Upload Evidence

```bash
curl -X POST http://localhost:8000/api/v1/evidence/upload \
  -F "file=@screenshot.png"
```

**Response:**
```json
{
  "url": "/uploads/a1b2c3d4-e5f6-7890-abcd-ef1234567890.png",
  "message": "Evidence uploaded and metadata scrubbed."
}
```

### Track a Report

```bash
curl http://localhost:8000/api/v1/reports/track/WD-K7M2-X9PL
```

**Response:**
```json
{
  "category": "CORRUPTION",
  "status": "SUBMITTED",
  "status_note": null,
  "status_update": null,
  "messages": [],
  "created_at": "2026-10-07T04:00:00Z",
  "updated_at": "2026-10-07T04:00:00Z"
}
```

### Moderator Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "moderator", "password": "moderator123"}'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

### List Reports (Moderator)

```bash
export TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

curl http://localhost:8000/api/v1/moderator/reports \
  -H "Authorization: Bearer $TOKEN"
```

### Advance Status (Moderator)

```bash
curl -X PATCH http://localhost:8000/api/v1/moderator/reports/1/status \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "UNDER_REVIEW", "status_update": "Assigned to primary investigator."}'
```

### Post Dead Drop Message (Moderator)

```bash
curl -X POST http://localhost:8000/api/v1/moderator/reports/1/messages \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": "Can you provide the specific account numbers involved?"}'
```

### Reply via Dead Drop (Whistleblower)

```bash
curl -X POST http://localhost:8000/api/v1/reports/track/WD-K7M2-X9PL/messages \
  -H "Content-Type: application/json" \
  -d '{"content": "Accounts 4401 and 4402 in the offshore ledger."}'
```

### Permanently Close a Case (Moderator)

```bash
curl -X POST http://localhost:8000/api/v1/moderator/reports/1/close \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status_note": "Case permanently archived after forensic review."}'
```

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
- End-to-end smoke tests covering the full application lifecycle, dashboard serving, OpenAPI completeness, and evidence integration

---

## Design Assumptions

1. **Single-server deployment**: SQLite is the storage backend. For multi-instance deployments, swap to PostgreSQL or another networked database.
2. **No reporter accounts**: Anonymity is enforced by design. Whistleblowers authenticate solely through possession of their Case Code.
3. **In-memory rate limiting**: Rate limit state is not shared across processes. Production deployments behind multiple workers should use an external store (e.g., Redis).
4. **Ephemeral JWT secret**: The default JWT secret is for development. Production deployments must set `JWT_SECRET_KEY` to a cryptographically random value.
5. **Local evidence storage**: Uploaded files are stored on the local filesystem. Production deployments may integrate with object storage (e.g., S3, GCS) for durability.
6. **Trust boundary**: Moderators are trusted users authenticated via JWT. There is no role hierarchy or audit trail for moderator actions.

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
