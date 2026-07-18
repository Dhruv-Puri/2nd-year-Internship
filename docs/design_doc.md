# Architecture Design Document: EventHub

**Author:** Dhruv Puri 
**Date:** 18 July 2026  
**Segment:** Segment 4 — Foundations of Cloud & DevOps  
**Problem Statement:** J2 — Internal Tool Backbone  

## 1. System Overview
EventHub is an internal event management tool built to streamline how university student clubs organize gatherings, manage RSVPs, and track attendance. It replaces chaotic WhatsApp/Google Form workflows with a centralized, role-based platform.

**Week 3 Mini-Extension (Automated Notifications):** The platform extends standard CRUD operations by integrating a production-grade transactional email pipeline using **Azure Communication Services (ACS)**. This powers secure OTP-based user registration, password resets, automated RSVP confirmations, 24-hour event reminders, and attendance finalization receipts. To prevent API abuse during demos, the system is protected by a custom `EmailQuota` database guardrail and a global frontend toggle.

**AI Extension (EventBot):** A lightweight, guardrailed `/api/bot/ask` endpoint provides students with instant, rule-based answers to common event queries, serving as the foundational seed for a future Retrieval-Augmented Generation (RAG) implementation.

---

## 2. Cloud Infrastructure Topology

The system uses a highly decoupled, cloud-native architecture. Frontend assets are served via edge caching, the API handles business logic and authentication, and external cloud services handle specialized workloads (email delivery).

```mermaid
graph TD
    %% Define Styles
    classDef azure fill:#0072C6,stroke:#fff,stroke-width:2px,color:#fff;
    classDef db fill:#00bcba,stroke:#fff,stroke-width:2px,color:#fff;
    classDef cicd fill:#24292e,stroke:#fff,stroke-width:2px,color:#fff;
    classDef acs fill:#FFD21E,stroke:#000,stroke-width:2px,color:#000;
    
    User((User Browser))

    subgraph Frontend Tier
        SWA["Azure Storage Account<br/>Static Website Hosting<br/>HTML/CSS/JS"]:::azure
    end

    subgraph CI/CD Pipeline
        GH["GitHub Actions"]:::cicd
        GHCR[("GitHub Container<br/>Registry")]:::cicd
    end

    subgraph Backend Tier
        API["Azure App Service<br/>FastAPI Container"]:::azure
    end

    subgraph Data & Services Tier
        DB[("Azure PostgreSQL<br/>Flexible Server")]:::db
        ACS["Azure Communication<br/>Services"]:::acs
    end

    %% Routing
    User -->|"1. HTTP GET (Assets)"| SWA
    User -->|"2. REST API + Bearer JWT"| API
    API -->|"3. Read/Write Data (SQLAlchemy)"| DB
    API -->|"4. Send OTPs & Reminders"| ACS
    
    GH -->|"5. Docker Build & Push"| GHCR
    GHCR -->|"6. Webhook / Pull Image"| API
```

---

## 3. Tech Stack Matrix

| Component | Technology | Rationale |
| --- | --- | --- |
| **Backend API** | FastAPI (Python 3.11+) | High-throughput asynchronous framework with native Pydantic validation and auto-generated OpenAPI documentation. |
| **Database** | Azure PostgreSQL | Enterprise-grade relational engine for enforcing strict constraints across Users, Clubs, Events, and RSVPs. |
| **Frontend** | HTML / CSS / Vanilla JS | Zero-dependency, lightweight static assets optimized for fast edge delivery via Azure Storage Account. |
| **Authentication** | JWT + Bcrypt + OTP | Secure, stateless token-based security paired with time-bound OTP verification to prevent database bloat from unverified accounts. |
| **Notification Engine** | Azure Communication Services (ACS) | Native Azure integration for transactional emails without the strict domain-verification friction of third-party providers like SendGrid. |
| **Cloud Hosting** | Azure PaaS Ecosystem | Platform-as-a-Service deployment that cleanly decouples frontend and backend infrastructure while maintaining unified billing and IAM. |

---

## 4. Core System Flows

### Flow A: Stateless Authentication & OTP Verification
This flow details how the decoupled frontend securely handles registration via OTP, stores the JWT, and routes the user without leaving traces in the browser history stack.

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant UI as Frontend (Azure Storage)
    participant API as FastAPI (Azure App Service)
    participant DB as PostgreSQL
    participant ACS as Azure Comm. Services

    User->>UI: Enters Email, Password, Role
    UI->>API: POST /api/auth/register
    API->>DB: Check if email exists. If no, generate 6-digit OTP.
    API->>DB: Store pending user data + OTP in OTP table.
    API->>ACS: Trigger OTP Email via Connection String.
    ACS-->>API: 202 Accepted
    API-->>UI: 200 OK "OTP Sent"
    
    User->>UI: Enters OTP Code
    UI->>API: POST /api/auth/verify-otp
    API->>DB: Validate OTP code and expiration time.
    alt Invalid/Expired OTP
        API-->>UI: 400 Bad Request
    else Valid OTP
        API->>DB: Create actual User record. Delete OTP record.
        API->>API: Generate Signed JWT
        API-->>UI: 200 OK {access_token: "..."}
        UI->>UI: Save to localStorage
        Note over UI: window.location.replace() prevents back-button bypass
        UI->>User: Redirect to dashboard.html
    end
```

### Flow B: Event Lifecycle & Guardrails
This flow demonstrates how the system prevents data corruption once an event's attendance is finalized.

```mermaid
sequenceDiagram
    autonumber
    actor Admin
    participant UI as Frontend
    participant API as FastAPI
    participant DB as PostgreSQL

    Admin->>UI: Clicks "Submit Attendance" for Event X
    UI->>API: POST /api/admin/events/{id}/submit-attendance
    API->>DB: Check if event.attendance_submitted == True
    alt Already Submitted
        API-->>UI: 400 Bad Request "Attendance already locked"
    else Not Submitted
        API->>DB: Set event.attendance_submitted = True
        API->>DB: Loop through RSVPs, trigger ACS email stubs for attendance status.
        API-->>UI: 200 OK "Attendance Finalized"
        Note over API,DB: Subsequent DELETE/PUT requests for this event are now blocked by backend guardrails.
    end
```

---

## 5. Database Schema & Entity Relationships

The PostgreSQL database enforces relational integrity across all entities. The following Entity-Relationship (ER) diagram maps the cardinality, including the new tables for OTP, Notifications, Announcements, and Email Quotas.

```mermaid
erDiagram
    USER {
        int id PK
        string email UK
        string name
        string role
        string hashed_password
    }
    CLUB {
        int id PK
        string name UK
    }
    EVENT {
        int id PK
        string title
        int club_id FK
        datetime start_time
        boolean attendance_submitted
        boolean reminder_sent
    }
    RSVP {
        int id PK
        int user_id FK
        int event_id FK
        datetime created_at
    }
    ATTENDANCE {
        int id PK
        int rsvp_id FK
        boolean is_present
        datetime checked_in_at
    }
    OTP {
        int id PK
        string email
        string code
        datetime expires_at
        string name
        string role
        string hashed_password
    }
    NOTIFICATION {
        int id PK
        int user_id FK
        string message
        boolean is_read
        datetime created_at
    }
    ANNOUNCEMENT {
        int id PK
        int club_id FK
        int author_id FK
        string title
        string content
        datetime created_at
    }
    EMAIL_QUOTA {
        int id PK
        string date UK
        int count
        boolean is_valid
    }

    USER ||--o{ CLUB : "manages/joins (M2M)"
    CLUB ||--o{ EVENT : "hosts"
    USER ||--o{ RSVP : "submits"
    EVENT ||--o{ RSVP : "receives"
    RSVP ||--o| ATTENDANCE : "has"
    USER ||--o{ NOTIFICATION : "receives"
    CLUB ||--o{ ANNOUNCEMENT : "posts"
```

---

## 6. Security & Governance Posture

To ensure platform integrity and data privacy, EventHub implements security at multiple layers:

1. **Network Level (CORS):** The FastAPI backend explicitly defines allowed origins. Only requests originating from the verified Azure Storage Account domain will be processed, mitigating Cross-Site Request Forgery (CSRF).
2. **Data Layer (Cryptographic Hashing):** All passwords are one-way hashed using `Bcrypt` with a dynamic salt before reaching the database. Plain-text passwords never exist in memory post-validation.
3. **Session Layer (Stateless Auth):** JSON Web Tokens (JWT) are signed using a server-side secret (`HS256`). They carry a strict 60-minute expiration payload to ensure stale sessions are automatically invalidated.
4. **Business Logic Guardrails:** 
   - **Temporal Buffers:** Events cannot be created or edited to start in less than 3 hours.
   - **State Locking:** Once `attendance_submitted` is true, all `DELETE` and `PUT` requests for that event or its RSVPs are hard-blocked at the API level.
   - **Abuse Prevention:** The `EmailQuota` model hard-limits outbound ACS emails to 10 per day, with a global toggle to disable the pipeline instantly for demo environments.

---

## 7. CI/CD Deployment Strategy (DevOps Core)

As a Cloud & DevOps-focused project, manual deployments are replaced by automated GitHub Actions pipelines.

```mermaid
graph LR
    %% Styles
    classDef git fill:#24292e,stroke:#fff,stroke-width:2px,color:#fff;
    classDef test fill:#e3b341,stroke:#000,stroke-width:2px,color:#000;
    classDef deploy fill:#0072C6,stroke:#fff,stroke-width:2px,color:#fff;

    Push["Push to main"]:::git --> Action["GitHub Actions Trigger"]:::git
    Action --> Lint["Code Linting &amp; PyTest"]:::test
     
    Lint -->|Passes| BuildAPI["Build FastAPI Docker Image"]:::deploy
    BuildAPI --> PushGHCR["Push to GitHub Container Registry"]:::deploy
    PushGHCR --> DeployAPI["Azure App Service Pulls Image &amp; Restarts"]:::deploy
    
    Lint -->|Passes| SyncUI["Sync Static Assets"]:::deploy
    SyncUI --> DeployUI["Azure Storage Account (Static Website)"]:::deploy
```

**Pipeline Stages:**
1. **Trigger:** Activated on direct merges to the `main` branch.
2. **Validation:** Runs `pytest` to ensure core CRUD, Auth, and Guardrail logic is unbroken.
3. **Delivery:** If tests pass, GitHub Actions builds the Docker image, pushes it to GHCR, and triggers the Azure App Service deployment webhook.

---

## 8. Directory Blueprint

```text
.
├── backend/
│   └── app/
│       ├── auth.py            # JWT token creation, Bcrypt hashing, role checkers
│       ├── database.py        # SQLAlchemy engine, session lifecycle
│       ├── email_extension.py # ACS integration, EmailQuota guardrails, notification logic
│       ├── main.py            # FastAPI entry point, CORS config, all API endpoints
│       ├── models.py          # SQLAlchemy ORM models (Users, Clubs, Events, OTP, etc.)
│       └── schemas.py         # Pydantic data validation schemas
├── frontend/              
│   ├── index.html             # Tabbed Login/Signup/OTP interface
│   ├── index.css              # Authentication styling & animations
│   ├── index.js               # Auth logic, OTP handling, theme persistence
│   ├── dashboard.html         # Role-based dashboard (Student/Admin/Coordinator)
│   ├── dashboard.css          # CSS Variables, Dynamic Theming, Responsive Layout
│   └── dashboard.js           # State management, authFetch wrapper, DOM manipulation
├── tests/
│   └── test_auth.py           # Pytest suite for backend guardrails
├── docs/
│   ├── ADR-001.md             # Decoupled Vanilla JS Frontend with JWT
│   ├── ADR-002.md             # Unified Azure PaaS Ecosystem
│   ├── AAD-003.md             # Azure ACS & Guardrails for Transactional Emails
│   └── design_doc.md          # This file
├── .env.example               # Template for environment variables
├── .gitignore                 # Protects .env, .venv, and local artifacts
├── requirements.txt           # Python dependencies
└── README.md                  # Project overview, quickstart, and architecture
```

---

## 9. Core API Endpoints Specification

**Authentication & Users**
* `POST /api/auth/register` - Initiates registration, generates OTP, stores pending data, triggers ACS email.
* `POST /api/auth/verify-otp` - Validates OTP, creates actual User record, returns JWT.
* `POST /api/auth/login` - Validates credentials and returns JWT.
* `POST /api/auth/forgot-password` & `POST /api/auth/reset-password` - Secure password recovery via OTP.
* `GET /api/users/me` - Validates JWT and returns current user data.

**Event Core Functions**
* `POST /api/admin/events` - Club Admins create events (enforces 3-hour temporal buffer).
* `GET /api/events/upcoming` - Students fetch events for clubs they have joined.
* `POST /api/events/{id}/rsvp` - Students register for an event (triggers ACS confirmation email).
* `POST /api/admin/events/{id}/submit-attendance` - Locks the event, prevents further mutations, and triggers bulk attendance status emails.

**Coordinator & System**
* `GET /api/coordinator/reports` - Aggregated analytics (attendance rates, top events, club metrics).
* `PUT /api/system/toggle-email` - Global switch to enable/disable the ACS email pipeline for demo safety.
* `POST /api/system/send-reminders` - Cron-triggerable endpoint to blast 24-hour event reminders.
* `POST /api/bot/ask` - Guardrailed, context-based endpoint for student event queries.

---

## 10. Next Milestones for Architecture Review

1. **CI/CD Finalization:** Complete the GitHub Actions workflow to seamlessly build, test, push to GHCR, and deploy to Azure App Service without manual intervention.
2. **EventBot Enhancement:** Expand the `/api/bot/ask` endpoint from simple keyword matching to a lightweight, guardrailed context-based API (or basic RAG) to handle complex student queries about club rulebooks.
3. **Schema Migrations:** Transition from `Base.metadata.create_all()` to `Alembic` for version-controlled, production-safe database schema migrations within the CI/CD pipeline.
