# 🛡️ WhistleDrop

> **Confidential, Zero-Knowledge Anonymous Reporting & Encrypted Dead Drops.**  
> *What if an anonymous reporting system was leaked, but the attacker learned literally nothing?*  
> WhistleDrop provides complete whistleblower anonymity through cryptographic zero-knowledge lookups, in-memory EXIF metadata scrubbing, and automated data minimization on permanent closure.

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.14+-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Tests](https://img.shields.io/badge/Tests-79%20Passing-brightgreen.svg?logo=pytest&logoColor=white)](#-running-tests)
[![Architecture](https://img.shields.io/badge/Architecture-Zero--Knowledge-purple.svg)](#-threat-model--security-architecture)
[![Zero Setup](https://img.shields.io/badge/Setup-Zero--Friction%20(uv%20%2B%20SQLite)-orange.svg)](#-quickstart-in-30-seconds)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[**⚡ 30s Quickstart**](#-quickstart-in-30-seconds) &bull;
[**🎯 2-Minute Evaluator Tour**](#-2-minute-evaluator-tour) &bull;
[**✨ Key Features**](#-key-features--technical-capabilities) &bull;
[**🔄 Technical Workflow**](#-end-to-end-technical-workflow) &bull;
[**🛡️ Security Architecture**](#-threat-model--security-architecture) &bull;
[**📖 API & Docs**](#-api-reference)

</div>

<!-- HERO DEMO VIDEO PLACEHOLDER -->
<div align="center">

https://github.com/user-attachments/assets/a7a13480-5399-43e3-9e5a-3a31e2cb3aaa

*🎥 **Interactive Product Tour**: Anonymous submission, zero-knowledge lookup, moderator split-view triage, and ADR-0002 permanent case closure.*

</div>

---

## ⚡ Quickstart in 30 Seconds

Zero external databases, zero containers required to run locally. Built with Python 3.14, FastAPI, SQLite, and `uv`.

```bash
# 1. Clone repository & install dependencies
git clone https://github.com/libin-codes/whistle-drop.git
cd whistle-drop
uv sync

# 2. Launch the backend server
uv run uvicorn app.main:app --reload
```

Instant access points:
* 🖥️ **Embedded Dashboard (Zero-setup UI)**: [http://localhost:8000](http://localhost:8000)
* 📑 **Interactive Swagger API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
* 🧪 **Run 79 Automated Tests**: `uv run pytest` *(completes in < 4s)*

*(Prefer Docker? Run `docker compose up --build` and open [http://localhost:8000](http://localhost:8000))*

---

## 🎯 2-Minute Evaluator Tour


### 1. Submit an Anonymous Report
* Open [http://localhost:8000](http://localhost:8000).
* In the **Submit Report** tab, choose a category (e.g. `CORRUPTION`), provide details, and optionally drag-and-drop an image into the evidence dropzone.
* Click **Submit Report Securely**.
* In the **Report Submitted Securely** modal, copy your cryptographically random **Case Code** (e.g. `WD-K7M2-X9PL`). *This secret token is revealed only once and never persisted in plaintext.*



### 2. Triage as Moderator in the Split Inspector
* In the top-right header, click **Moderator Login** (next to the Whistleblower persona badge).
* Log in using default auto-seeded credentials:
  * **Username:** `moderator`
  * **Password:** `moderator123`
* In the **Triage Reports Queue**, test the toolbar search and category/status filter dropdowns.
* Click your report's row (marked with a trailing chevron) to open the **Report Inspector**:
  * **Consolidated Overview Card**: Inspect the Report ID, Category badge, Submitted timestamp, description box, and scrubbed evidence preview.
  * **Status Workflow (Left Column)**: Enter a public status update note (e.g. `"Assigned to senior investigator"`) and click **Move to UNDER_REVIEW**.
  * **Dead Drop Thread (Right Column)**: Post an inquiry or guidance message to the whistleblower.




### 3. Track & Reply as Whistleblower
* Switch to the **Track Report** tab.
* Paste your `Case Code` and click **Track Case**.
* Observe the interactive 4-stage **Workflow Stepper**, read the moderator's public status update callout, and send an anonymous reply through the **Dead Drop** message thread.



### 4. Verify Permanent Closure & Data Minimization (ADR-0002)
* Return to the Moderator Inspector and scroll to **Permanent Case Closure & Data Minimization**.
* Click **Irreversibly Close Case** and confirm in the warning dialog modal.
* Observe [ADR-0002](docs/adr/0002-permanent-closure-data-minimization.md) in action:
  * The description is irreversibly overwritten with `[REDACTED - CASE PERMANENTLY CLOSED]`.
  * The attached evidence file is physically shredded and unlinked from disk.
  * The Dead Drop message thread is permanently frozen against further writes.



### 5. Verify the Test Suite
* In your terminal, run `uv run pytest`. All **79 automated tests** covering zero-knowledge hashing, in-memory EXIF scrubbing, rate limiting, and closure immutability pass immediately.

---

## ✨ Key Features & Technical Capabilities

WhistleDrop combines cryptographic privacy, in-memory metadata sanitization, and automated data minimization into a unified, zero-friction reporting platform.

### 🔒 1. Zero-Knowledge Ingestion & Lookups ([ADR-0001](docs/adr/0001-hashed-case-codes.md))
* **Ephemeral Secret Issuance**: Whistleblowers receive an 8-character cryptographically random Case Code (`WD-XXXX-XXXX`, >41 bits of entropy) revealed exactly once upon submission.
* **Zero Plaintext Persistence**: The server hashes the code using SHA-256 in-memory and stores solely the cryptographic digest. Even with a full database dump, attackers cannot recover plaintext Case Codes or read reports without the whistleblower's secret token.
* **Accountless Authentication**: Zero accounts, cookies, sessions, or IP addresses linked to submissions. Possession of the Case Code is the sole authenticator.

### 🧹 2. In-Memory Evidence Sanitization
* **Pre-Disk EXIF Stripping**: Image uploads (`image/jpeg`, `image/png`, `image/webp`) are buffered directly in memory.
* **Device & Location Neutralization**: Pillow re-encodes pure pixel data, permanently stripping device serial numbers, camera model data, software signatures, and GPS latitude/longitude coordinates before writing to disk.
* **UUID Isolation**: Uploaded evidence files are assigned random UUID names on disk to prevent filesystem metadata correlation.

### 📬 3. Bi-Directional Anonymous Dead Drop
* **Asynchronous Communication**: Enables secure back-and-forth messaging between moderators and whistleblowers without identity linkage.
* **Zero-Knowledge Whistleblower Access**: The reporter fetches and posts to their private Dead Drop channel simply by providing their plaintext Case Code (hashed on the fly).
* **Role-Tagged Attribution**: Messages distinguish between `WHISTLEBLOWER` and `MODERATOR` personas without exposing moderator personal identifiers or requiring whistleblower credentials.

### 🚦 4. Deterministic Forward-Only State Machine
* **Guaranteed Lifecycle**: Case status progresses forward through a strictly controlled state machine (`SUBMITTED` → `UNDER_REVIEW` → `RESOLVED` / `DISMISSED` → `PERMANENTLY_CLOSED`).
* **No Backtracking or Skip Mutations**: Invalid state jumps or backward transitions are rejected with `HTTP 400 Bad Request`.
* **Public Status Updates**: Every transition allows moderators to publish status update notes visible to the whistleblower via their tracking stepper.

### 💥 5. Automated Data Minimization on Closure ([ADR-0002](docs/adr/0002-permanent-closure-data-minimization.md))
* **Irreversible Redaction**: Transitioning to `PERMANENTLY_CLOSED` immediately overwrites the case description with a standardized Redaction Marker: `[REDACTED - CASE PERMANENTLY CLOSED]`.
* **Physical Evidence Shredding**: Associated evidence files are physically unlinked and removed from disk storage (`os.remove`).
* **Immutable Thread Lock**: Dead Drop message threads are permanently frozen against subsequent writes, and case status is permanently sealed against future modifications.

### 📊 Capability Matrix: WhistleDrop vs. Traditional Systems

| Capability | Traditional Helpdesks & Forms | WhistleDrop |
|---|---|---|
| **Reporter Identity** | Requires email, account, or IP tracking | **Zero accounts, zero tracking**. Possession of secret Case Code is the sole authenticator. |
| **Database Compromise** | Plaintext tracking IDs reveal case channels | **Zero-Knowledge SHA-256 Storage ([ADR-0001](docs/adr/0001-hashed-case-codes.md))**. Leaked database reveals zero Case Codes. |
| **Evidence Metadata** | Stores raw uploads containing GPS, camera EXIF | **In-Memory Evidence Scrubbing**. EXIF/GPS metadata is stripped in-memory before disk persistence. |
| **Brute-Force Protection** | Often unprotected enumeration | **Sliding-Window Rate Limiter**. Throttles tracking to 10 req/min per IP (~7,000 years to exhaust space). |
| **Case Closure** | Soft deletes or retains sensitive data indefinitely | **Permanent Closure Minimization ([ADR-0002](docs/adr/0002-permanent-closure-data-minimization.md))**. Physical file shredding & description tombstoning. |
| **Two-Way Communication** | Requires user accounts or email chains | **Anonymous Dead Drop Thread**. Bi-directional asynchronous messaging authenticated only by Case Code. |
| **Setup & Evaluation** | Requires Node, Postgres, Redis, complex configs | **Zero-Friction ([ADR-0003](docs/adr/0003-python-fastapi-stack.md))**. Single command launch via `uv` or Docker with embedded SPA dashboard. |

---

## 🔄 End-to-End Technical Workflow

The diagram below illustrates the end-to-end data lifecycle across actors, in-memory processing pipelines, and persistence tiers:

```
┌───────────────┐          ┌───────────────────────┐          ┌─────────────────────┐          ┌───────────────┐
│ Whistleblower │          │ FastAPI Service (Mem) │          │ Storage (DB / Disk) │          │   Moderator   │
└───────┬───────┘          └───────────┬───────────┘          └──────────┬──────────┘          └───────┬───────┘
        │                              │                                 │                             │
 [PHASE 1: INGESTION & ZERO-KNOWLEDGE GENERATION]                        │                             │
        │                              │                                 │                             │
        │ 1. POST /evidence/upload     │                                 │                             │
        ├─────────────────────────────►│ In-Memory Pillow Re-encode      │                             │
        │                              │ (Strip EXIF, GPS, Serial)       │                             │
        │                              ├────────────────────────────────►│ Write /uploads/<uuid>.jpg   │
        │ 2. POST /reports             │                                 │                             │
        ├─────────────────────────────►│ Generate Code: WD-K7M2-X9PL     │                             │
        │                              │ Compute SHA256(Code)            │                             │
        │                              │ Discard Plain Code from Memory  │                             │
        │                              ├────────────────────────────────►│ INSERT INTO reports         │
        │                              │                                 │ (hashed_code, SUBMITTED)    │
        │◄─────────────────────────────┤                                 │                             │
        │ Return WD-K7M2-X9PL (once)   │                                 │                             │
        │                              │                                 │                             │
 [PHASE 2: TRIAGE & FORWARD STATUS WORKFLOW]                             │                             │
        │                              │                                 │                             │
        │                              │                                 │   3. POST /auth/login       │
        │                              │◄──────────────────────────────────────────────────────────────┤
        │                              │ Issue JWT (HS256, 24h)          │                             │
        │                              ├──────────────────────────────────────────────────────────────►│
        │                              │                                 │   4. GET /moderator/reports │
        │                              │◄──────────────────────────────────────────────────────────────┤
        │                              ├────────────────────────────────►│ SELECT * FROM reports       │
        │                              │ Return triage queue             │                             │
        │                              ├──────────────────────────────────────────────────────────────►│
        │                              │                                 │   5. PATCH /reports/{id}    │
        │                              │◄──────────────────────────────────────────────────────────────┤
        │                              │ Validate State Transition       │                             │
        │                              ├────────────────────────────────►│ UPDATE status=UNDER_REVIEW  │
        │                              │                                 │   6. POST /dead-drop        │
        │                              │◄──────────────────────────────────────────────────────────────┤
        │                              ├────────────────────────────────►│ INSERT message (MODERATOR)  │
        │                              │                                 │                             │
 [PHASE 3: ZERO-KNOWLEDGE TRACKING & DEAD DROP REPLY]                    │                             │
        │                              │                                 │                             │
        │ 7. GET /reports/track/{code} │                                 │                             │
        ├─────────────────────────────►│ Check Sliding-Window Rate Limit │                             │
        │                              │ Compute SHA256(code)            │                             │
        │                              ├────────────────────────────────►│ SELECT WHERE hashed_code    │
        │◄─────────────────────────────┤ Return status stepper & thread  │                             │
        │ 8. POST /track/{code}/msg    │                                 │                             │
        ├─────────────────────────────►│ Compute SHA256(code)            │                             │
        │                              ├────────────────────────────────►│ INSERT message (REPORTER)   │
        │◄─────────────────────────────┤ HTTP 201 Created                │                             │
        │                              │                                 │                             │
 [PHASE 4: ADR-0002 PERMANENT CLOSURE & DATA MINIMIZATION]               │                             │
        │                              │                                 │                             │
        │                              │                                 │   9. POST /reports/{id}/cls │
        │                              │◄──────────────────────────────────────────────────────────────┤
        │                              │ Validate Status Machine         │                             │
        │                              │ Trigger Shredder & Tombstone    │                             │
        │                              ├────────────────────────────────►│ 10. os.remove(evidence_path)│
        │                              ├────────────────────────────────►│ 11. description = [REDACTED]│
        │                              ├────────────────────────────────►│ 12. Lock thread & status    │
        │                              │ Confirm ADR-0002 Minimization   │                             │
        │                              ├──────────────────────────────────────────────────────────────►│
        ▼                              ▼                                 ▼                             ▼
```

### Technical Lifecycle Breakdown

1. **Phase 1: Ingestion & Ephemeral Token Generation**
   * Whistleblower submits payload (`POST /api/v1/reports`, optional image `POST /api/v1/evidence/upload`).
   * Image payload is buffered in-memory; Pillow reconstructs raw pixel data to purge all metadata headers (`EXIF`, `GPS`, `Make`, `Model`, `Software`) before writing with a random UUID name to `/uploads/`.
   * Server generates a cryptographically random Case Code (`WD-XXXX-XXXX`), computes its SHA-256 digest, and persists solely `Hashed Case Code` to SQLite.
   * The plaintext Case Code is returned in the HTTP 201 response and immediately discarded from application memory.

2. **Phase 2: Moderator Triage & Forward State Progression**
   * Moderator authenticates (`POST /api/v1/auth/login`) and receives a 24-hour HS256 JWT bearer token.
   * Moderator queries the triage queue (`GET /api/v1/moderator/reports`), filtering by category or lifecycle status.
   * Moderator advances status (`PATCH /api/v1/moderator/reports/{id}/status`) from `SUBMITTED` to `UNDER_REVIEW`, attaching public status updates.
   * Moderator initiates inquiries via the Dead Drop message thread (`POST /api/v1/moderator/reports/{id}/messages`).

3. **Phase 3: Zero-Knowledge Dead Drop Exchange**
   * Whistleblower queries `/api/v1/reports/track/{case_code}`.
   * The sliding-window rate limiter enforces a strict 10 req/min limit per IP to neutralize brute-force key-space sweeps.
   * Backend computes SHA-256 of the supplied Case Code in-memory, queries SQLite by digest, and returns the case stepper and message history.
   * Whistleblower posts anonymous follow-ups (`POST /api/v1/reports/track/{case_code}/messages`) authenticated exclusively through Case Code possession.

4. **Phase 4: ADR-0002 Terminal Destruction & Minimization**
   * Moderator invokes permanent closure (`POST /api/v1/moderator/reports/{id}/close`).
   * Status transitions to terminal `PERMANENTLY_CLOSED`.
   * The report's detailed description is irreversibly overwritten in the database with the Redaction Marker (`[REDACTED - CASE PERMANENTLY CLOSED]`).
   * Attached evidence files on disk are immediately unlinked and removed (`os.remove`).
   * The Dead Drop thread is frozen; any future writes from either moderator or whistleblower return `HTTP 400 Bad Request`.

## 🛡️ Threat Model & Security Architecture

### 1. Zero-Knowledge Case Codes ([ADR-0001](docs/adr/0001-hashed-case-codes.md))

```
Whistleblower                     WhistleDrop Backend                     Database
    │                                      │                                  │
    │  Submit Report                       │                                  │
    ├─────────────────────────────────────►│  Generate Code: WD-K7M2-X9PL    │
    │                                      │  Hash Code: SHA256(...)          │
    │                                      │─────────────────────────────────►│
    │  Returns Plain Code: WD-K7M2-X9PL    │                                  │ Store ONLY Hash
    │◄─────────────────────────────────────┤                                  │ (Plain code discarded)
    │                                      │                                  │
```

* Plaintext Case Codes (`WD-XXXX-XXXX`, 8 alphanumeric characters = ~41 bits of entropy) are returned to the reporter **once** and never persisted.
* The database stores only the irreversible SHA-256 digest (`Hashed Case Code`).
* Lookups hash the incoming code in-memory. Even if a rogue database administrator dumps the full SQLite database, **they cannot access or view reports without knowing the plaintext Case Code**.

### 2. In-Memory Evidence Scrubbing

```
Uploaded Image (JPEG/PNG/WebP)
┌─────────────────────────────────┐
│ [EXIF: iPhone 15 Pro, GPS Lat/Lng]│
│ [Device Serial, Timestamp]      │
│ [Image Pixel Data]              │
└────────────────┬────────────────┘
                 │ Pillow In-Memory Re-encoding (Zero disk writes of raw file)
                 ▼
Scrubbed File on Disk (/uploads/<uuid>.jpg)
┌─────────────────────────────────┐
│ [Clean Pixel Data ONLY]         │
└─────────────────────────────────┘
```

* All uploaded images undergo validation for allowed MIME types (`image/jpeg`, `image/png`, `image/webp`) and a 5 MB size limit.
* Pillow loads image bytes in-memory and re-encodes pure pixel data, stripping EXIF, GPS coordinates, camera serial numbers, and software signatures before saving to disk with a UUID.

### 3. Data Minimization on Permanent Closure ([ADR-0002](docs/adr/0002-permanent-closure-data-minimization.md))

* Advancing a case to `PERMANENTLY_CLOSED`:
  1. Overwrites report description with standardized Redaction Marker: `[REDACTED - CASE PERMANENTLY CLOSED]`.
  2. Physically unlinks and shreds attached evidence files from disk.
  3. Freezes the Dead Drop message thread against any subsequent messages.
  4. Permanently locks report status (subsequent updates or modifications return `HTTP 400 Bad Request`).

---

## 🏗️ Architecture & Component Design

```
┌────────────────────────────────────────────────────────────────────────┐
│                        WhistleDrop Stack                               │
│                                                                        │
│  ┌────────────────────────┐  ┌──────────────────────────────────────┐  │
│  │ Embedded Dashboard SPA │  │        FastAPI Application           │  │
│  │       (GET /)          │  │                                      │  │
│  └────────────────────────┘  │  ┌──────────┐ ┌───────────┐ ┌──────┐ │  │
│                              │  │ Reports  │ │ Evidence  │ │ Auth │ │  │
│  ┌────────────────────────┐  │  │  Router  │ │  Router   │ │Router│ │  │
│  │ Interactive Swagger UI │  │  └────┬─────┘ └─────┬─────┘ └──┬───┘ │  │
│  │      (GET /docs)       │  │       │             │          │     │  │
│  └────────────────────────┘  │  ┌────┴─────────────┴──────────┴───┐ │  │
│                              │  │        Moderator Router         │ │  │
│                              │  └──────────────────┬──────────────┘ │  │
│                              │                     │                │  │
│                              │  ┌──────────────────┴──────────────┐ │  │
│                              │  │   Domain Services & Validation  │ │  │
│                              │  │ case_codes │ workflow │ rate_lim│ │  │
│                              │  │ evidence   │ auth     │ database│ │  │
│                              │  └──────────────────┬──────────────┘ │  │
│                              │                     │                │  │
│                              │  ┌──────────────────┴──────────────┐ │  │
│                              │  │ SQLite Database (whistledrop.db)│ │  │
│                              │  └─────────────────────────────────┘ │  │
│                              └──────────────────────────────────────┘  │
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                /uploads/ (Local Scrubbed Evidence Storage)       │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 📖 API Reference

All primary endpoints live under `/api/v1`. Full interactive OpenAPI documentation and live execution is available at [`http://localhost:8000/docs`](http://localhost:8000/docs).

| Method | Endpoint | Access | Purpose |
|---|---|---|---|
| `POST` | `/api/v1/reports` | Anonymous | Submit anonymous report; returns plaintext Case Code once |
| `GET` | `/api/v1/reports/track/{case_code}` | Anonymous (Rate-limited) | Look up report status via zero-knowledge code hash |
| `POST` | `/api/v1/reports/track/{case_code}/messages` | Anonymous (Rate-limited) | Post whistleblower reply to Dead Drop thread |
| `GET` | `/api/v1/reports/track/{case_code}/messages` | Anonymous (Rate-limited) | Retrieve Dead Drop thread for case |
| `POST` | `/api/v1/evidence/upload` | Anonymous | Upload evidence image (automatic EXIF/GPS scrubbing) |
| `POST` | `/api/v1/auth/login` | Public | Authenticate moderator; returns 24h JWT Bearer token |
| `GET` | `/api/v1/moderator/reports` | Moderator (JWT) | List reports with category/status filters & pagination |
| `GET` | `/api/v1/moderator/reports/{id}` | Moderator (JWT) | Retrieve full details for single report |
| `PATCH` | `/api/v1/moderator/reports/{id}/status` | Moderator (JWT) | Advance report through Status Workflow state machine |
| `POST` | `/api/v1/moderator/reports/{id}/messages` | Moderator (JWT) | Post moderator inquiry to report Dead Drop |
| `GET` | `/api/v1/moderator/reports/{id}/messages` | Moderator (JWT) | Read report Dead Drop thread |
| `POST` | `/api/v1/moderator/reports/{id}/close` | Moderator (JWT) | Permanently close case & trigger data minimization |

<details>
<summary><b>📜 Click to view cURL Examples for Key Endpoints</b></summary>

<br>

### 1. Submit an Anonymous Report
```bash
curl -X POST http://localhost:8000/api/v1/reports \
  -H "Content-Type: application/json" \
  -d '{
    "category": "CORRUPTION",
    "description": "Unusual fund transfers identified in Q3 budget allocations."
  }'
```

### 2. Upload Evidence (EXIF-Scrubbed)
```bash
curl -X POST http://localhost:8000/api/v1/evidence/upload \
  -F "file=@screenshot.png"
```

### 3. Track Report Status
```bash
curl http://localhost:8000/api/v1/reports/track/WD-K7M2-X9PL
```

### 4. Moderator Login
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "moderator", "password": "moderator123"}'
```

### 5. Advance Status (Moderator)
```bash
curl -X PATCH http://localhost:8000/api/v1/moderator/reports/1/status \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"status": "UNDER_REVIEW", "status_update": "Assigned to primary investigator."}'
```

### 6. Post Dead Drop Message (Whistleblower)
```bash
curl -X POST http://localhost:8000/api/v1/reports/track/WD-K7M2-X9PL/messages \
  -H "Content-Type: application/json" \
  -d '{"content": "Relevant accounts are 4401 and 4402."}'
```

### 7. Permanently Close Case (Moderator)
```bash
curl -X POST http://localhost:8000/api/v1/moderator/reports/1/close \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"status_note": "Case permanently archived after forensic review."}'
```

</details>

---

## 🧪 Running Tests

The test suite contains **79 automated tests** covering security invariants, state machines, and end-to-end user journeys:

```bash
uv run pytest
```

Output:
```text
tests/test_auth.py .....                                                 [  6%]
tests/test_case_closure.py ........                                      [ 16%]
tests/test_case_codes.py ....                                            [ 21%]
tests/test_dead_drop.py ......                                           [ 29%]
tests/test_evidence.py ........                                          [ 39%]
tests/test_moderator_reports.py ........                                 [ 49%]
tests/test_reports.py ..........                                         [ 62%]
tests/test_smoke_e2e.py ..............                                   [ 79%]
tests/test_status_workflow.py ...........                                [ 93%]
tests/test_tracking.py .....                                             [100%]

============================== 79 passed in 4.03s ==============================
```

Test coverage includes:
* **Zero-Knowledge Hashing**: Verifying deterministic SHA-256 digests and zero plain-token persistence.
* **Metadata Scrubbing**: Asserting stripping of EXIF tags (`Make`, `Model`, `Software`, GPS coordinates) on upload.
* **Rate Limiting**: Sliding-window 429 enforcement under rapid sequential tracking requests.
* **Status Workflow**: Validating forward-only state progression and rejection of illegal status jumps.
* **Permanent Closure Minimization**: Verifying description tombstone replacement, evidence file disk unlinking, and post-closure write freeze.
* **E2E Smoke Tests**: Full report creation to moderation, messaging, and closure flow.

---

## ⚙️ Configuration & Environment

| Variable | Default | Purpose |
|---|---|---|
| `JWT_SECRET_KEY` | `whistledrop-jwt-moderator-secret-key-32b` | Secret key for signing HS256 JWT tokens |
| `MODERATOR_USERNAME` | `moderator` | Default auto-seeded moderator username |
| `MODERATOR_PASSWORD` | `moderator123` | Default auto-seeded moderator password |

---

## 📚 Domain Language & Documentation

WhistleDrop adheres to a ubiquitous domain vocabulary and recorded architecture decisions:

* [GLOSSARY.md](GLOSSARY.md): Canonical domain terms (`Report`, `Case Code`, `Hashed Case Code`, `Dead Drop`, `Status Workflow`, `Permanent Closure`, `Evidence Scrubbing`, `Redaction Marker`).
* [ADR-0001: Hashed Case Codes for Zero-Knowledge Tracking](docs/adr/0001-hashed-case-codes.md)
* [ADR-0002: Data Minimization on Permanent Case Closure](docs/adr/0002-permanent-closure-data-minimization.md)
* [ADR-0003: Python, FastAPI, and SQLite for Backend Stack](docs/adr/0003-python-fastapi-stack.md)

---

## 📄 License

MIT &copy; 2026 Libin
