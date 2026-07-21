# 🎟️ EventHub: Internal Tool Backbone + AI Chat - Extension
> *A centralized, cloud-native platform for university student clubs to organize events, manage RSVPs, and query event guidelines using an integrated AI assistant.*

**Author:** Dhruv  
**Segment:** Segment 4 — Foundations of Cloud & DevOps  
**Problem Statement Code:** J2 (Internal Tool Backbone)  
---

# 📹 Demo & Live Deployment

| Asset | Link |
| :--- | :--- |
| **Live Frontend URL** | [https://<your-storage-account>.z13.web.core.windows.net](#) |
| **Live Backend API** | [https://<your-webapp-name>.azurewebsites.net/docs](#) |
| **3-Minute Video Walkthrough** | [Google-Drive Link Here](#) |

> ⚠️ **Note:** The backend runs on Azure App Service (Free Tier) which cold-starts after ~5 minutes of inactivity. The first API call may take 30-60 seconds. Subsequent requests are instant.

---

# 📋 Problem Statement

**Business Scenario:** You are a Junior Backend/DevOps Engineer at "ClubHub" — the platform that runs LPU's 200+ student clubs. Currently, clubs manage events with Google Forms + WhatsApp groups, which is chaos. The Student Affairs office wants a simple internal tool: a club-event manager where clubs can create events, students can RSVP, attendance is tracked, and reports are auto-generated.

**What EventHub Delivers:**
- **Club Admins** can create/edit/delete events, view RSVPs, mark attendance, export CSV reports, and post announcements.
- **Students** can browse upcoming events from joined clubs, RSVP, cancel RSVPs, view their event history, and receive email notifications.
- **Coordinators** can manage clubs, assign/revoke admin access, feature events, and view institutional analytics (attendance rates, top events, events per club).
- **All roles** authenticate via secure email/password + OTP verification, with stateless JWT-based sessions.

---

# 🏗️ Architecture Diagram

```mermaid
graph TD
    %% Define Styles
    classDef azure fill:#0072C6,stroke:#fff,stroke-width:2px,color:#fff;
    classDef db fill:#00bcba,stroke:#fff,stroke-width:2px,color:#fff;
    classDef local fill:#24292e,stroke:#fff,stroke-width:2px,color:#fff;
    classDef acs fill:#FFD21E,stroke:#000,stroke-width:2px,color:#000;

    User((User Browser))

    subgraph "Frontend Tier (Static)"
        SWA["Azure Storage Account<br/>Static Website Hosting<br/>HTML / CSS / Vanilla JS"]:::azure
    end

    subgraph "Backend Tier (Containerised)"
        API["Azure App Service<br/>FastAPI Docker Container<br/>Port 8000"]:::azure
    end

    subgraph "Data & Services Tier"
        DB_LOCAL[("PostgreSQL 16<br/>(Local via Docker Compose)")]:::local
        DB_CLOUD[("Neon PostgreSQL<br/>(Serverless Cloud - Free Tier)")]:::db
        ACS["Azure Communication<br/>Services (Email)"]:::acs
    end

    User -->|"1. HTTP GET (Static Assets)"| SWA
    User -->|"2. REST API + Bearer JWT"| API
    API -->|"3a. Read/Write (Local Dev)"| DB_LOCAL
    API -->|"3b. Read/Write (Production)"| DB_CLOUD
    API -->|"4. OTP / RSVP / Reminder Emails"| ACS
```

## Architecture Explanation

EventHub follows a **fully decoupled, three-tier architecture**:

1. **Frontend Tier:** Pure HTML/CSS/Vanilla JS static assets served via Azure Storage Account's built-in Static Website hosting. Zero build step, zero framework dependencies. A `config.js` file dynamically injects the backend API URL at runtime, enabling the same codebase to work locally (via Docker Compose on `localhost:8000`) and in production (pointing to the Azure Web App URL).

2. **Backend Tier:** A FastAPI application containerised with Docker, deployed to Azure App Service for Containers. The container listens on port 8000 and exposes 30+ REST endpoints with auto-generated OpenAPI documentation at `/docs`.

3. **Data & Services Tier:**
   - **Local Development:** PostgreSQL 16 runs inside a Docker Compose service, providing a zero-config local database.
   - **Production Deployment:** Neon PostgreSQL (Serverless, Free Tier) provides a production-grade relational database without the cost of Azure Database for PostgreSQL.
   - **Email Delivery:** Azure Communication Services (ACS) handles all transactional emails — OTP verification, RSVP confirmations, attendance receipts, and 24-hour event reminders.


---

# 🛠️ Tech Stack

| Component | Technology | Why (Rationale) |
| :--- | :--- | :--- |
| **Backend Framework** | FastAPI (Python 3.11) | High-throughput async framework with native Pydantic validation, auto-generated OpenAPI docs, and dependency injection for clean testable code. |
| **Database (Local)** | PostgreSQL 16 (Docker) | Enterprise-grade relational engine for enforcing strict constraints across Users, Clubs, Events, RSVPs. Runs in Docker Compose for zero-config local setup. |
| **Database (Cloud)** | Neon PostgreSQL (Free Tier) | Serverless Postgres with auto-pause/resume. Chosen over Azure Database for PostgreSQL to strictly adhere to the 100% free-tier constraint while maintaining production-grade SQL. |
| **Frontend** | HTML / CSS / Vanilla JS | Zero-dependency, lightweight static assets. No build step, no node_modules, no framework lock-in. Optimised for instant edge delivery via Azure Storage. |
| **Authentication** | JWT (HS256) + Bcrypt + OTP | Stateless token-based auth with 60-minute expiry. Passwords hashed with Bcrypt. OTP verification prevents database bloat from unverified accounts. |
| **Email Engine** | Azure Communication Services | Native Azure integration for transactional emails. Avoids SendGrid's strict domain-verification friction. Protected by a custom `EmailQuota` guardrail (10 emails/day limit). |
| **Containerisation** | Docker + Docker Compose | Single `docker-compose up` command spins up the entire stack (PostgreSQL + FastAPI + Nginx frontend) for any reviewer. |
| **Cloud Hosting** | Azure PaaS (App Service + Storage) | Platform-as-a-Service deployment that cleanly decouples frontend and backend infrastructure. |
| **ORM** | SQLAlchemy 2.0 | Python's most mature ORM with declarative models, relationship management, and session handling. |
| **Testing** | Pytest + FastAPI TestClient | 6 test files, 20+ test cases covering auth flows, RBAC guardrails, event lifecycle, RSVP logic, and coordinator reports. |

---

# 🚀 Quickstart

> A reviewer must be able to go from `git clone` to a running product in **< 20 minutes**.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) (v24+)
- [Docker Compose](https://docs.docker.com/compose/install/) (v2.20+)
- That's it. No Python, no Node, no PostgreSQL installation needed.


## Install
### Option A: Docker Compose (Recommended — Zero Config)

```bash
# 1. Clone the repository
git clone https://github.com/<your-username>/2nd-year-Internship.git
cd 2nd-year-Internship

# 2. Start the entire stack (Database + Backend + Frontend)
docker-compose up --build

# 3. Access the application
#    Frontend:  http://localhost:8080
#    Backend API: http://localhost:8000/docs
#    PostgreSQL: localhost:5432 (user: eventhub, pass: eventhub, db: eventhub)
```

**What happens under the hood:**
- `db` service: Pulls `postgres:16-alpine`, creates the `eventhub` database, waits for health check.
- `api` service: Builds the FastAPI Docker image, connects to the `db` service via Docker's internal network, auto-creates all tables via SQLAlchemy, and starts Uvicorn on port 8000.
- `web` service: Pulls `nginx:alpine`, mounts the `./frontend` directory as read-only static files, serves on port 8080.

> 💡 The `config.js` file has an empty `API_URL` by default. The frontend JavaScript automatically falls back to `http://127.0.0.1:8000` when `API_URL` is empty, which is exactly where Docker Compose exposes the backend. **No manual configuration needed.**

### Option B: Manual Setup (For Development)

```bash
# 1. Clone and enter the project
git clone https://github.com/<your-username>/2nd-year-Internship.git
cd 2nd-year-Internship

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your values (see "Environment Variables" section below)

# 5. Start PostgreSQL (via Docker or local install)
docker run -d --name eventhub-db \
  -e POSTGRES_USER=eventhub \
  -e POSTGRES_PASSWORD=eventhub \
  -e POSTGRES_DB=eventhub \
  -p 5432:5432 \
  postgres:16-alpine

# 6. Start the backend
uvicorn backend.app.main:app --reload --port 8000

# 7. Serve the frontend (any static file server)
cd frontend
python -m http.server 8080
# OR use VS Code Live Server extension on index.html
```

### Environment Variables

Create a `.env` file in the project root:

```env
# JWT Configuration
SECRET_KEY=your-super-secret-jwt-key-change-this
ALGORITHM=HS256

# Database (Local Docker Compose overrides this automatically)
DATABASE_URL=postgresql://eventhub:eventhub@localhost:5432/eventhub

# Azure Communication Services (Email)
ACS_CONNECTION_STRING=endpoint=https://<resource>.communication.azure.com/;accesskey=<key>
SENDER_EMAIL=DoNotReply@<your-domain>.azurecomm.net

# CORS (comma-separated allowed origins)
ALLOWED_ORIGINS=http://localhost:8080,http://127.0.0.1:8080
```

> ⚠️ The `.env.example` file ships with empty values intentionally. Docker Compose overrides `DATABASE_URL`, `SECRET_KEY`, and `ALGORITHM` with working defaults so any reviewer can run the app without configuring anything.

## Running Tests

```bash
# From the project root
pytest -v

# Expected output: 20+ tests passing across 6 test files
# Tests use an isolated SQLite database (test_eventhub.db) — no external DB needed
```

**Test Coverage:**
| Test File | What It Validates |
| :--- | :--- |
| `test_auth.py` | Registration, OTP verification, login, duplicate prevention, password reset, protected routes |
| `test_coordinator.py` | Club creation, admin assignment, report generation, RBAC enforcement |
| `test_e2e_flow.py` | Full lifecycle: club → admin → event → student → RSVP → attendance → reports |
| `test_events_guardrails.py` | 3-hour temporal buffer, club access control, role-based restrictions |
| `test_rsvp_attendance.py` | RSVP flow, duplicate prevention, attendance locking, cancel restrictions |
| `test_system.py` | Bot endpoint, email toggle, reminder system |


---

## 🔌 API Endpoints (30+ Documented)

Full interactive documentation available at: `http://localhost:8000/docs` (local) or `https://<webapp>.azurewebsites.net/docs` (production).

## Authentication & Users
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| POST | `/api/auth/register` | Register with email/password → triggers OTP email |
| POST | `/api/auth/verify-otp` | Verify OTP → creates account → returns JWT |
| POST | `/api/auth/login` | Login with credentials → returns JWT |
| POST | `/api/auth/forgot-password` | Send password reset OTP |
| POST | `/api/auth/reset-password` | Reset password with OTP |
| GET | `/api/users/me` | Get current user profile (protected) |

## Student Operations
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| GET | `/api/events/upcoming` | Browse events from joined clubs (with search) |
| POST | `/api/events/{id}/rsvp` | RSVP to an event (triggers confirmation email) |
| DELETE | `/api/events/{id}/rsvp` | Cancel RSVP (blocked if attendance locked) |
| GET | `/api/users/me/rsvps` | View my active RSVPs |
| POST | `/api/clubs/{id}/join` | Join a club |
| DELETE | `/api/clubs/{id}/leave` | Leave a club |

## Admin Operations
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| POST | `/api/admin/events` | Create event (3-hour buffer enforced) |
| PUT | `/api/admin/events/{id}` | Update event (blocked if attendance locked) |
| DELETE | `/api/admin/events/{id}` | Delete event (blocked if attendance locked) |
| GET | `/api/admin/events/{id}/rsvps` | View RSVPs for an event |
| POST | `/api/admin/events/{id}/attendance` | Mark individual attendance |
| POST | `/api/admin/events/{id}/submit-attendance` | Lock attendance (triggers bulk emails) |
| GET | `/api/admin/events/{id}/export-csv` | Download attendance CSV |
| GET | `/api/admin/stats` | View club statistics |
| POST | `/api/clubs/{id}/announcements` | Post club announcement |

## Coordinator Operations
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| GET | `/api/coordinator/reports` | Institutional analytics dashboard |
| POST | `/api/clubs` | Create a new club |
| PUT | `/api/clubs/{id}` | Update club name |
| DELETE | `/api/clubs/{id}` | Delete club (cascades to events) |
| POST | `/api/clubs/{id}/assign-admin` | Assign admin to club |
| DELETE | `/api/clubs/{id}/revoke-admin` | Revoke admin access |
| POST | `/api/events/{id}/feature` | Toggle featured status |

## System & Notifications
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| GET | `/api/notifications` | Get user notifications |
| GET | `/api/announcements` | Get announcements for joined clubs |
| PUT | `/api/system/toggle-email` | Enable/disable email pipeline |
| POST | `/api/system/send-reminders` | Trigger 24-hour reminder emails |
| POST | `/api/bot/ask` | Ask EventBot a question (rule-based) |

---

## 🐳 Docker & Containerisation

### Dockerfile (Backend)
* File 1 - **[Dockerfile](Dockerfile)** (for cloud hosting and via github actions)

The backend is containerised using a multi-stage-optimised single-stage Dockerfile:


**Key Design Decisions:**
- `python:3.11-slim` base keeps the image under 200MB.
- `PYTHONUNBUFFERED=1` ensures logs stream in real-time to Azure's log viewer.
- `HEALTHCHECK` enables Azure App Service to detect container readiness.
- Only `backend/app` is copied (not tests, docs, or frontend) — minimal attack surface.

### Docker Compose (Local Development)
* File 2 - **[docker-compose.yml](docker-compose.yml)** (for the entire tech stack to help build everything locally without complex commands)


**How it works:**
1. `db` starts first and waits until `pg_isready` confirms PostgreSQL is accepting connections.
2. `api` builds from the Dockerfile, connects to `db` via Docker's internal DNS (`db:5432`), auto-creates tables, and starts serving.
3. `web` mounts the `./frontend` directory read-only into Nginx, serving static files on port 8080.
4. The frontend's `config.js` has an empty `API_URL`, so JavaScript falls back to `http://127.0.0.1:8000` — exactly where the `api` service is exposed.

**Result:** Any reviewer with Docker installed can run `docker-compose up --build` and have the full application running in under 2 minutes with zero configuration.

---

## ✨ Mini-Extension: Automated Notification Pipeline (Azure Communication Services)

For the Week 3 Mini-Extension, I moved beyond simple "stubbed" console logs and integrated a **real, production-grade transactional email pipeline** using Azure Communication Services (ACS).

### What It Does

| Trigger | Email Sent |
| :--- | :--- |
| User registers | 6-digit OTP code (expires in 15 minutes) |
| User requests password reset | Reset OTP code |
| Student RSVPs to event | "RSVP Confirmed: {event title}" |
| Admin submits attendance | Bulk email to all RSVP'd students with Present/Absent status |
| 24 hours before event | Reminder email to all registered students |

### Engineering Highlights

1. **Real Email Delivery:** Uses the `azure-communication-email` SDK with a verified sender domain. Not a mock — actual emails arrive in the recipient's inbox.

2. **Abuse Prevention (`EmailQuota` Model):** A database-backed guardrail hard-limits the system to **10 emails per day**. Once exceeded, emails are logged to console instead of sent. This prevents accidental quota exhaustion during demos or testing.

3. **Global Toggle Switch:** A frontend toggle (top-left of the login page) and a backend endpoint (`PUT /api/system/toggle-email`) allow instantly enabling/disabling the entire email pipeline. Useful for demo environments where you don't want to spam real inboxes.

4. **OTP-Based Registration:** Instead of creating unverified user accounts that bloat the database, the system stores pending registration data in a separate `OTP` table. Only after successful OTP verification is the actual `User` record created. Expired OTPs are cleaned up automatically.

5. **In-App Notifications:** Alongside emails, every significant action (RSVP, cancellation, attendance finalization, event deletion) creates an in-app notification stored in the `Notification` table, accessible via the bell icon in the dashboard.

---

## 🔐 Security & Guardrails

| Layer | Implementation |
| :--- | :--- |
| **Password Storage** | Bcrypt with dynamic salt. Plain-text never persists. |
| **Authentication** | JWT (HS256) with 60-minute expiry. Stateless — no server-side session store. |
| **Authorization** | Role-based access control (student/admin/coordinator) via `require_role()` dependency. |
| **Club Isolation** | Admins can only manage events for clubs they're explicitly assigned to (`verify_admin_club_access`). |
| **Temporal Buffers** | Events cannot be created/edited to start less than 3 hours from now. |
| **State Locking** | Once `attendance_submitted = True`, all DELETE/PUT operations on that event and its RSVPs are hard-blocked. |
| **CORS** | Backend explicitly whitelists allowed origins. Only the Azure Storage domain (or localhost for dev) can make API calls. |
| **Email Rate Limiting** | Maximum 10 outbound emails per day per deployment. |
| **OTP Expiry** | All OTP codes expire after 15 minutes. |

---

## 📂 Project Structure

```
2nd-year-Internship/
├── .github/
│   └── workflows/
│       ├── backend-ci-cd.yml          # Backend: test → build → push → deploy
│       └── frontend-deploy.yml        # Frontend: config injection → upload to Azure Storage
├── docs/
│   ├── adr/
│   │   ├── ADR-001.md                 # Decoupled Vanilla JS Frontend
│   │   ├── ADR-002.md                 # Neon PostgreSQL for Cloud Deployment
│   │   └── ADR-003.md                 # Azure Communication Services for Emails
│   └── design_doc.md                  # Full architecture design document
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── auth.py                    # JWT, Bcrypt, RBAC dependencies
│   │   ├── database.py                # SQLAlchemy engine, session, Base
│   │   ├── email_extension.py         # ACS email client, quota logic, notifications
│   │   ├── main.py                    # FastAPI app, all 30+ endpoints
│   │   ├── models.py                  # SQLAlchemy ORM models (9 tables)
│   │   └── schemas.py                 # Pydantic request/response schemas
│   └── tests/
│       ├── conftest.py                # Fixtures, test DB setup, email mocking
│       ├── test_auth.py               # Auth flow tests (6 tests)
│       ├── test_coordinator.py        # Coordinator RBAC tests (2 tests)
│       ├── test_e2e_flow.py           # Full lifecycle E2E test (1 test)
│       ├── test_events_guardrails.py  # Temporal/access guardrail tests (4 tests)
│       ├── test_rsvp_attendance.py    # RSVP + attendance lock tests (2 tests)
│       └── test_system.py             # Bot, toggle, reminders tests (3 tests)
├── frontend/
│   ├── config.js                      # Runtime API URL injection (empty for local)
│   ├── index.html                     # Login/Register/OTP/Forgot Password page
│   ├── index.css                      # Auth page styles + 5 themes
│   ├── index.js                       # Auth logic, OTP flow, email toggle
│   ├── dashboard.html                 # Role-based dashboard (Student/Admin/Coordinator)
│   ├── dashboard.css                  # Dashboard styles + responsive design
│   └── dashboard.js                   # All dashboard logic, overlays, charts
├── .dockerignore
├── .env.example                       # Template with empty values (intentional)
├── docker-compose.yml                 # Full local stack (DB + API + Frontend)
├── Dockerfile                         # Backend container image
├── pytest.ini                         # Test configuration
├── requirements.txt                   # Python dependencies
├── queries.sql                        # Reference SQL queries
└── README.md                          # This file
```

---

# 📊 Data Sources

The application uses **synthetic seed data** for initial demonstration. On first run, the database is empty. Users can:
1. Register as a **Coordinator** → Create clubs → Assign admins.
2. Register as an **Admin** → Create events for assigned clubs.
3. Register as a **Student** → Join clubs → Browse and RSVP to events.

All data persists in PostgreSQL (local) or Neon PostgreSQL (production). No external APIs or datasets are required.

---

# 📂 Architecture Decision Records (ADRs)

All major architectural choices are documented with context, decisions, consequences, and alternatives considered:

- **[ADR-001: Decoupled Vanilla JS Frontend with Runtime Config Injection](./docs/adr/ADR-001.md)**
- **[ADR-002: Neon PostgreSQL (Serverless) for Cloud + Local PostgreSQL via Docker](./docs/adr/ADR-002.md)**
- **[ADR-003: Azure Communication Services (ACS) for Transactional Emails](./docs/adr/ADR-003.md)**

---

# ⚠️ Known Limitations

1. **JWT in LocalStorage:** Tokens are stored in `localStorage` for ease of cross-origin decoupled testing. In a production environment, these should be migrated to `HttpOnly` cookies to mitigate XSS risks.

2. **Synchronous Email Sending:** ACS API calls are currently synchronous within the request handler. In production, these should be offloaded to FastAPI `BackgroundTasks` or an Azure Service Bus queue to prevent blocking the main API thread.

3. **No Schema Migrations:** Database tables are created using `Base.metadata.create_all()`. For production with evolving schemas, Alembic should be integrated for version-controlled migrations.

4. **Neon Cold Start:** The Neon free-tier database auto-pauses after ~10 minutes of inactivity. The first request after a pause takes 2-3 seconds. `pool_pre_ping=True` in SQLAlchemy handles this gracefully, but users may notice a brief delay.

5. **Single-Instance Deployment:** The Azure App Service runs a single container instance. No horizontal scaling, load balancing, or redundancy is configured (appropriate for the free tier scope).

6. **EventBot is Rule-Based:** The `/api/bot/ask` endpoint currently uses simple keyword matching. A context-aware LLM integration (Google Gemini API) is planned as the next enhancement.

---

# 🔮 What I'd Do in 3rd Year

This project serves as the foundational seed for my 3rd-year portfolio. Next year, I plan to:

- **Multi-tenancy:** Isolate club data securely with row-level security policies.
- **Full RAG Pipeline:** Replace the rule-based bot with Retrieval-Augmented Generation using Azure AI Search + LangChain, allowing students to "chat" with event rulebooks.
- **Observability:** Add Prometheus + Grafana + OpenTelemetry for distributed tracing and metrics.
- **Kubernetes Migration:** Move from single-container App Service to Azure Kubernetes Service (AKS) with horizontal pod autoscaling.
- **GitOps CI/CD:** Implement ArgoCD for declarative, automated deployments.

*(See `docs/roadmap_3rd_year.md` for the detailed 12-month plan.)*

---

## 📜 License & Acknowledgements

- **License:** MIT License
- **Acknowledgements:** Built as part of the 2nd Year B.Tech CSE-AIDE Internship Program (Foundations of Cloud & DevOps). Special thanks to my segment mentor for guidance on Azure PaaS networking, API guardrails, and DevOps best practices.


