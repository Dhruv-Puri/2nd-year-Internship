# Design Document: EventHub (J2)

**Author:** Dhruv  
**Date:** 24 June 2026  
**Segment:** Segment 4 — Foundations of Cloud & DevOps  
**Problem Statement:** J2 — Internal Tool Backbone  

---

## 1. Overview
EventHub is an internal event management tool built to streamline how university student clubs organize gatherings, manage RSVPs, and track attendance. It replaces disjointed workflows with a centralized platform tailored for club admins, students, and coordinators. 

To enforce platform integrity without complex ML overhead, the system implements a secure **Domain-Restricted Magic Link** authentication flow, restricting platform access exclusively to verified university email addresses.

---

## 2. Tech Stack

| Component | Technology | Rationale |
| :--- | :--- | :--- |
| **Backend API** | FastAPI (Python 3.11+) | Asynchronous performance, native Pydantic validation, and auto-generated OpenAPI documentation. |
| **Database** | PostgreSQL | Relational storage ideal for handling complex constraints between users, events, and RSVPs. |
| **Frontend** | [Streamlit OR Next.js] | Interface for administrative actions, browsing events, and viewing operational reports. |
| **Authentication** | JWT + SMTP (SendGrid / AWS SES) | Stateless token-based security paired with passwordless email verification. |
| **Containerization** | Docker & Docker Compose | Multi-container encapsulation ensuring identical environments across local dev and production. |
| **CI/CD** | GitHub Actions | Automated pipeline execution for linting, testing, and deployment webhooks. |
| **Monitoring** | Uptime Kuma | External health checking, response time tracking, and instant alerting. |

---

## 3. Architecture Design

The system follows a containerized micro-services architecture managed via Docker Compose. Security boundaries are enforced at the network level, isolating the database from direct public access.

           [ Public Internet ]
                   │
                   ▼ (Port 80/443)
       ┌────────────────────────────────┐
       │         Frontend UI            │
       │    (Streamlit / Next.js)       │
       └───────────┬────────────▲───────┘
                   │            │
                   │ (REST API) │ (JWT Auth Check)
                   ▼            │
       ┌────────────────────────────────┐
       │        FastAPI Backend         │ ◄───► [ External SMTP Service ]
       │         (App Container)        │       (SendGrid / AWS SES)
       └───────────┬────────────▲───────┘
                   │            │
                   │ (SQL)      │ (Internal Net)
                   ▼            │
       ┌────────────────────────────────┐
       │       PostgreSQL Database      │
       │        (Data Container)        │
       └────────────────────────────────┘

### Network Segments:
* **Public Network:** Exposes the Frontend UI to the browser.
* **Internal Application Network:** Bridges the Frontend and FastAPI backend container securely.
* **Data Network:** Isolated network tier allowing *only* the FastAPI container to query the PostgreSQL instance.

---

## 4. Core System Flows

### Flow A: Passwordless Authentication (Magic Link)

    [User Browser]             [FastAPI Backend]            [SMTP Server]
          │                            │                          │
          ├─────── 1. Enter Email ────►│                          │
          │       (name@lpu.co.in)     ├─ 2. Validate Domain      │
          │                            ├─ 3. Generate Secure JWT  │
          │                            │                          │
          │                            ├──── 4. Send Link ───────►│ ───► [Dispatches Email]
          │◄────── 5. 200 OK ──────────┤                          │
          │                            │                          │
     [Clicks Email Link]               │                          │
          │                            │                          │
          ├─────── 6. GET /verify ────►├─ 7. Parse & Verify JWT   │
          │◄────── 8. Issue Session ───┤                          │

### Flow B: Event Registration & Notification Engine

    [Student Browser]          [FastAPI Backend]          [PostgreSQL]          [SMTP Server]
          │                            │                       │                     │
          ├─────── 1. POST /rsvp ─────►│                       │                     │
          │                            ├─ 2. Check Capacity ──►│                     │
          │                            │◄─ 3. Capacity OK ─────┤                     │
          │                            │                       │                     │
          │                            ├─ 4. Record RSVP ─────►│                     │
          │                            │                       │                     │
          │                            ├───────────────────────┼──────── 5. Trigger ─► [Send Grid]
          │◄────── 6. RSVP Success ────┤                       │                     │      │
                                                                                            ▼
                                                                                    [Sends Receipt Email]

---

## 5. Directory Structure Blueprint

A clean layout ensuring modularity and compliance with the 2nd-year production framework:

    ├── .github/
    │   └── workflows/
    │       └── ci-cd.yml          # GitHub Actions deployment pipeline
    ├── backend/
    │   ├── app/
    │   │   ├── main.py            # FastAPI entry point & initialization
    │   │   ├── models.py          # SQLAlchemy / SQLModel database entities
    │   │   ├── schemas.py         # Pydantic data validation schemas
    │   │   ├── database.py        # Connection pooling and session lifecycle
    │   │   ├── config.py          # Environment configuration & secret handling
    │   │   ├── auth.py            # JWT token creation and validation mechanics
    │   │   └── services/
    │   │       └── notify.py      # Background async email notifications worker
    │   ├── tests/
    │   │   ├── test_auth.py       # Authentication unit tests
    │   │   └── test_events.py     # Core event logic integration tests
    │   ├── Dockerfile             # Multi-stage optimized build for backend service
    │   └── requirements.txt
    ├── frontend/                  # Streamlit or frontend files
    ├── docs/
    │   ├── adr/                   # Architecture Decision Records
    │   └── design_doc.md          # This file
    └── docker-compose.yml         # Defines app, db, and monitoring container coordination

---

## 6. Core API Endpoints Specification

The platform implements a RESTful API compliant with the required minimum feature threshold:

### Authentication & Users
* `POST /api/v1/auth/magic-login` - Receives email string, validates university domain, and dispatches magic link token via email.
* `GET /api/v1/auth/verify` - Consumes token string from magic link, verifies validity, and issues session token.

### Club Management
* `POST /api/v1/clubs` - Allows Coordinator to register a student club.
* `GET /api/v1/clubs/{id}` - Public endpoint retrieving metadata for a specific club profile.

### Event Core Functions
* `POST /api/v1/events` - Executed by Club Admins to post upcoming events.
* `GET /api/v1/events` - Public endpoint allowing students to search and browse current events.

### RSVPs & Engagement
* `POST /api/v1/events/{id}/rsvp` - Enables students to register a seat for an event (triggers notification service).
* `GET /api/v1/users/me/events` - Allows students to review their upcoming and past event schedules.

### Attendance & Reporting
* `POST /api/v1/events/{id}/attendance` - Allows Club Admins to toggle attendance markers for registered attendees.
* `GET /api/v1/reports/dashboard` - Restricted endpoint for Coordinators to parse metrics like attendance yield and top-performing clubs.

---

## 7. Next Milestones for Architecture Review
* **Rate-Limiting:** Implement an IP and email-based rate-limiter on the magic login route to counter malicious API abuse.
* **Asynchronous Offloading:** Ensure that the email dispatch logic runs as a background task in FastAPI so user request lifecycles are never slowed down by external SMTP latencies.
