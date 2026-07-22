# Reflection — EventHub (J2: Internal Tool Backbone)

**Author:** Dhruv Puri
**Date:** 25 July 2026
**Segment:** Segment 4 — Foundations of Cloud & DevOps
**Word Count:** ~1,400

---

## Section 1: What I Built

EventHub is a centralized, cloud-native event management platform for LPU's 200+ student clubs. It replaces the chaotic WhatsApp-group-and-Google-Form workflow with a structured, role-based system. Students browse events from clubs they've joined, RSVP with one click, and receive email confirmations. Club Admins create events, mark attendance, export CSV reports, and post announcements. Student Affairs Coordinators manage clubs, assign admins, feature events, and view institutional analytics like attendance rates and top-performing events. The entire system is protected by JWT-based authentication with OTP verification, role-based access control, club-level isolation, and temporal guardrails (events must be created 3+ hours in advance).

For the Week 3 Mini-Extension, I built a production-grade transactional email pipeline using Azure Communication Services (ACS). Instead of the "console stub" the problem statement suggested as the minimum, I integrated real email delivery for OTP verification, RSVP confirmations, attendance receipts, and 24-hour event reminders. To prevent abuse during demos and testing, I designed a three-layer guardrail system: a database-backed daily quota (10 emails/day), a global frontend toggle switch that defaults to OFF, and exception handling that gracefully degrades to console logging if ACS is unreachable. I also implemented an OTP-based registration architecture where unverified users never enter the User table — pending data lives in a transient OTP staging table that self-cleans on verification or expiry.

---

## Section 2: What I Learned About the Tools

**FastAPI** is not just "Flask with type hints." What surprised me was how the dependency injection system (`Depends()`) eliminates entire categories of bugs. When I write `admin: models.User = Depends(require_role("admin"))`, the framework handles token extraction, JWT decoding, database lookup, and role verification before my endpoint code even runs. I used to think middleware was the only way to do auth. Now I understand why FastAPI's approach is more testable — each dependency is a pure function I can override in tests. If I were telling a friend: "Start with the `/docs` page. Build one endpoint. Watch Pydantic reject bad input automatically. You'll never go back to manual validation."

**SQLAlchemy 2.0** taught me that ORMs are a double-edged sword. The declarative model syntax is beautiful — `Column(Integer, ForeignKey("clubs.id"))` reads like a schema definition. But relationships (`secondary=user_clubs`, `cascade="all, delete-orphan"`) have subtle behaviours that only reveal themselves at runtime. I spent an entire day debugging why deleting a Club threw an IntegrityError until I realised I needed to explicitly clear the M2M relationship before deletion. The lesson: ORMs abstract the SQL, but you still need to understand what SQL they're generating.

**Docker + Docker Compose** went from "mysterious black box" to "the first thing I set up in any project." The `depends_on: condition: service_healthy` pattern with PostgreSQL health checks was a revelation — no more "connection refused" errors because the API started before the database was ready. The `.dockerignore` whitelist pattern (exclude everything, then `!backend/app` and `!requirements.txt`) keeps the production image under 200MB. What I'd tell a friend: "Don't memorise Dockerfile syntax. Understand the layer caching model. Once you get that `COPY requirements.txt` before `COPY .` means dependency changes don't rebuild your entire image, everything else clicks."

**GitHub Actions** taught me that CI/CD is not just "run tests on push." The smoke test step — actually running the Docker container and curling `/docs` with retries — caught a bug where the container built successfully but crashed on startup due to a missing environment variable. Without that step, I would have pushed a broken image to GHCR and Azure would have pulled it. The `concurrency: backend-production` group preventing parallel deployments is a small detail that prevents real production incidents.

---

## Section 3: What I Learned About Myself

The hardest part was not the code. It was the **architecture decisions that had to be made before writing any code.** Choosing between Streamlit and Vanilla JS for the frontend took me two full days of research, prototyping, and ADR writing. In hindsight, the decision was obvious (static hosting constraint eliminates Streamlit), but at the time, I kept second-guessing myself. I learned that writing an ADR *before* building forces you to articulate *why*, which prevents the "I'll just refactor it later" trap.

What I enjoyed most was the **backend guardrail engineering.** Designing the attendance-locking state machine (once `attendance_submitted = True`, all mutations are blocked), the 3-hour temporal buffer, the club isolation checks — this felt like real engineering. It's not CRUD. It's thinking about what a malicious or careless user could do and building walls. The race condition fix on 11 June (where stale frontend state allowed cancelling RSVPs after attendance was locked) was the most satisfying bug I solved.

What I hated was **CSS debugging.** The Firefox continuous refresh loop on 13 June, caused by `localStorage` throwing in certain contexts, cost me four hours. The theme system works beautifully now, but I do not enjoy pixel-pushing. I'd rather write ten backend endpoints than centre one div.

On scheduling: I procrastinated on Docker until Week 4 (20 July). The project worked locally via `uvicorn` and `python -m http.server` for three weeks. I kept telling myself "Docker is just packaging, I'll do it at the end." This was wrong. Dockerising on Day 1 would have caught environment issues earlier and made the CI/CD pipeline design more natural. The Neon PostgreSQL migration on 20 July was also late — I should have tested the cloud database connection string format (`postgres://` vs `postgresql://`) weeks earlier.

---

## Section 4: What I'd Do Differently

If I started over, I would **Dockerise on Day 1.** Not as an afterthought in Week 4. The `docker-compose.yml` should have been the first file I wrote, because it forces you to think about service boundaries, environment variables, and networking from the start. Every bug I hit in Week 4 (Neon connection strings, GHCR authentication, Azure App Service port configuration) would have surfaced in Week 1 if the container was my primary development environment.

I would also **write tests alongside features, not after.** My test suite was written in a single session on 22 July. If I had written `test_auth.py` on the same day I built the auth endpoints, I would have caught the OTP expiry edge case immediately instead of discovering it during manual testing.

What I wish my mentor had told me on Day 1: "The deployment is not the last 10% of the project. It's the first 10%. Design for deployment from the start, and everything else falls into place." The `config.js` injection pattern, the environment variable strategy, the CORS configuration — all of these were retrofit decisions that would have been natural if I'd started with "how will this run in production?"

---

## Section 5: What's Next — The 3rd Year Plan

EventHub is the seed of my 3rd-year portfolio. The architecture is intentionally extensible: the decoupled frontend can be swapped for React without touching the API, the SQLAlchemy models can migrate to Alembic-managed schemas, and the synchronous email pipeline can move to Azure Service Bus.

In 3rd year, I plan to add multi-tenancy (row-level security for club data isolation), replace the rule-based EventBot with a Google Gemini API integration using context injection, add observability (OpenTelemetry + Grafana), and migrate from single-container App Service to Azure Kubernetes Service. The detailed 12-month plan is in `docs/roadmap_3rd_year.md`.

This project taught me that "full-stack" doesn't mean "I can write React and FastAPI." It means I can design a system where the frontend, backend, database, email service, container registry, and CI/CD pipeline all work together without me manually SSH-ing into a server. That's the foundation I'm building on.
