# Mock Interview — 5 Q&A Pairs for 3rd Year Internship

**Author:** Dhruv Puri
**Date:** 25 July 2026
**Context:** Questions a 3rd-year internship interviewer might ask about EventHub

---

## Q1: "Why did you choose Vanilla JS over React for the frontend? Isn't that a step backwards?"

**A:** It was a deliberate constraint-driven decision, not a skill gap. The project deploys to Azure Storage Static Website, which serves pure static files. React would require a build step (`npm run build`), a `node_modules` directory (200MB+), and Node.js in the CI/CD pipeline. For a 2-page application (login + dashboard), that's disproportionate complexity.

The key engineering insight is the `config.js` runtime injection pattern. The committed file has `API_URL: ""`, and the frontend JavaScript falls back to `localhost:8000`. In production, the GitHub Actions pipeline overwrites `config.js` with the real Azure URL before uploading to blob storage. This means the same codebase works in both environments with zero build steps and zero manual configuration.

I documented this decision in ADR-001 with a weighted decision matrix comparing Vanilla JS, React+Vite, Streamlit, and Jinja2 SSR across five criteria. Vanilla JS scored 4.85/5.00. React scored 3.35. The 1.5-point gap is entirely from the "zero build step" and "reviewer onboarding < 20 min" constraints.

In 3rd year, if the frontend grows beyond 2 pages, I'd consider React. But for this scope, adding a framework would be over-engineering.

---

## Q2: "Your email pipeline has a 10-email/day limit. How would you design this for 200 clubs with 50 students each?"

**A:** The 10-email limit is a deliberate guardrail for the student project scope, not a technical limitation. For production scale, I'd make three changes:

**First, move to async delivery.** Currently, `client.begin_send()` is synchronous in the request handler. When an admin submits attendance for 50 students, the endpoint blocks for 5–10 seconds. I'd move this to FastAPI `BackgroundTasks` (simple) or an Azure Service Bus queue (production-grade). The endpoint returns immediately with "Attendance submitted, emails are being sent," and a background worker processes the queue.

**Second, make the quota configurable per deployment.** Instead of a hardcoded `10`, the limit would be an environment variable (`EMAIL_DAILY_LIMIT=5000`). The `EmailQuota` model already supports this — it's just one integer. For 200 clubs × 50 students × 5 email triggers, you'd need ~50,000 emails/day, which exceeds ACS free tier. At that scale, you'd negotiate an enterprise ACS plan or add a secondary provider (SendGrid) with failover.

**Third, add delivery tracking.** The current implementation fires and forgets. Production needs a `DeliveryReceipt` table tracking message IDs, delivery status (delivered/bounced/failed), and timestamps. ACS returns a poller with a message ID — I'd store that and poll for status asynchronously.

The architecture already supports all three changes without restructuring. The `send_email_stub` function is isolated in one file (`email_extension.py`), the quota check is a single database query, and the toggle is a boolean flag. Swapping the implementation is a 30-line change.

---

## Q3: "Explain how your CI/CD pipeline prevents broken code from reaching production."

**A:** The pipeline has four gates, and a deployment only happens if all four pass:

**Gate 1: Unit Tests.** `pytest -v` runs 18 tests across 6 files against an isolated SQLite database. All email calls are monkeypatched to no-ops. This validates auth flows, RBAC guardrails, event lifecycle logic, and the attendance-locking state machine. If any test fails, the pipeline stops. No Docker image is built.

**Gate 2: Docker Build.** The image is built from the root `Dockerfile` using `python:3.14-slim`. Only `backend/app` is copied — not tests, not docs, not the frontend. This validates that all imports resolve and the application code is self-contained.

**Gate 3: Smoke Test.** The built container is actually *run* with a SQLite database, and the pipeline curls `http://localhost:8000/docs` with `--retry 5 --retry-delay 3 --retry-connrefused`. This catches startup crashes that unit tests miss — like a missing environment variable or a broken import chain. I added this after a real incident where the container built successfully but crashed on startup because `DATABASE_URL` wasn't set.

**Gate 4: GHCR Push + Azure Deploy.** Only after the smoke test passes does the image get pushed to GitHub Container Registry (tagged with the commit SHA for immutability) and deployed to Azure App Service via the publish profile.

The `concurrency: backend-production` group ensures only one deployment runs at a time. If two pushes hit `main` within seconds, the second deployment waits for the first to complete. This prevents race conditions in the Azure App Service restart.

---

## Q4: "You store JWTs in localStorage. That's vulnerable to XSS. Why, and what would you do differently?"

**A:** Yes, `localStorage` is accessible to any JavaScript running on the page, making it vulnerable to XSS attacks. I chose it deliberately for this project because the frontend is served from a **different origin** (Azure Storage) than the API (Azure App Service). Cookie-based auth with `credentials: 'include'` requires careful CORS configuration (`Access-Control-Allow-Credentials: true`, explicit origin whitelisting, `SameSite=None; Secure`), and I prioritised getting the decoupled architecture working end-to-end over hardening the token storage mechanism.

For production, I'd migrate to **HttpOnly cookies** with `SameSite=Strict`. This requires three changes:

1. The `/api/auth/login` endpoint sets a `Set-Cookie` header instead of returning the token in the JSON body.
2. The `authFetch()` wrapper in `dashboard.js` adds `credentials: 'include'` to every fetch call.
3. The CORS middleware changes from `allow_origins=["*"]` to the explicit Azure Storage domain, with `allow_credentials=True`.

The `SameSite=Strict` attribute prevents the cookie from being sent on cross-site requests, mitigating CSRF. The `HttpOnly` flag prevents JavaScript from reading the cookie, mitigating XSS token theft. The tradeoff is that the token is no longer accessible to client-side code, so any logic that reads the token (like displaying "logged in as...") must call `/api/users/me` instead.

I documented this as Known Limitation #1 in the README and as a planned migration in the design doc's "Next Milestones" section.

---

## Q5: "Walk me through what happens when a student RSVPs to an event. Every layer."

**A:** Let me trace the full request path:

**1. Frontend (`dashboard.js`):** The student clicks "RSVP" on an event card. `handleRSVP(eventId)` calls `authFetch('/api/events/{id}/rsvp', { method: 'POST' })`. The `authFetch` wrapper reads the JWT from `localStorage`, attaches it as `Authorization: Bearer <token>`, and sends the request to the API URL from `config.js`.

**2. CORS (FastAPI middleware):** The request arrives from the Azure Storage origin. The `CORSMiddleware` checks it against `ALLOWED_ORIGINS` (the Azure Storage domain in production). If it matches, the request proceeds.

**3. Authentication (`get_current_user` dependency):** The `Depends(get_current_user)` dependency extracts the Bearer token, decodes it with `python-jose` using the `SECRET_KEY` and `HS256` algorithm, validates the 60-minute expiry, extracts the `sub` claim (email), and queries the `User` table. If any step fails, a 401 is returned.

**4. Business Logic (endpoint handler):** The endpoint checks three things: (a) the student hasn't already RSVP'd (duplicate check → 400), (b) the event exists (404 if not), (c) the event's `start_time` hasn't passed (400 if past). If all pass, a new `RSVP` record is inserted.

**5. Email Pipeline (`send_email_stub`):** The guardrail chain runs: (a) check `EmailQuota.is_valid` — if the global toggle is OFF, log to console and return. (b) check `EmailQuota.count < 10` — if quota exceeded, log to console and return. (c) if both pass, call `EmailClient.from_connection_string()` and `client.begin_send()` with the RSVP confirmation email. On success, increment `quota.count` and commit. On exception, log the error and continue — the app never crashes due to email failure.

**6. In-App Notification (`create_notification`):** A `Notification` record is inserted with the message "RSVP Confirmed: You are registered for {title}!" This is the redundant channel — if email fails, the student still sees the notification in the dashboard bell icon.

**7. Response:** The endpoint returns `{"status": "success", "message": "RSVP confirmed"}`. The frontend shows a toast notification, re-fetches events and RSVPs, and re-renders the dashboard. The event card's button changes from "RSVP (N going)" to "Cancel RSVP."

The entire flow takes < 500ms in production (excluding the 2–3s Neon cold start on first request after idle, which `pool_pre_ping=True` handles gracefully).
