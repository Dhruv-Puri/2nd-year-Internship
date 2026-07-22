# EventHub — 3rd Year Extension Roadmap

**Author:** Dhruv Puri
**Date:** 25 July 2026

---

## What this project is today

EventHub is a deployed, containerised club-event management platform (FastAPI + PostgreSQL + Vanilla JS) with OTP auth, role-based access control, an ACS email pipeline with quota guardrails, and a two-workflow GitHub Actions CI/CD system deploying to Azure PaaS. It serves three roles (Student, Admin, Coordinator) across 34 REST endpoints.

## The arc: where this could be by 3rd year internship (May 2027)

By May 2027, EventHub should be a **multi-tenant, observable, AI-augmented platform** running on Kubernetes with GitOps deployments. The rule-based EventBot becomes a context-aware Gemini-powered assistant. The synchronous email pipeline becomes an async event-driven system. The single-container deployment becomes an auto-scaling cluster. The goal is not "more features" — it's **production-grade engineering depth** that I can speak to in 3rd-year internship interviews at product companies.

---

## 3rd Year Semester Plan (Aug 2026 – Dec 2026)

### Milestone 1 (Aug–Sep 2026): Schema Migrations + Async Emails

- **What I'll add:**
  - Replace `Base.metadata.create_all()` with **Alembic** for version-controlled migrations
  - Move ACS `client.begin_send()` calls to **FastAPI `BackgroundTasks`**
  - Add `DeliveryReceipt` tracking table for email status (delivered/bounced/failed)
- **Tools I'll learn:** Alembic, FastAPI BackgroundTasks, async Python patterns
- **Time commitment:** 6–8 hours/week
- **Done looks like:** Schema changes deployed via `alembic upgrade head` in CI/CD. Attendance finalization endpoint returns in < 200ms regardless of RSVP count.

### Milestone 2 (Oct–Nov 2026): EventBot AI + Observability

- **What I'll add:**
  - Upgrade `/api/bot/ask` to **Google Gemini Free API** with context injection (event title, rules, description, club name)
  - Add **structured JSON logging** (request ID, user ID, endpoint, latency)
  - Add **OpenTelemetry** tracing with Azure Monitor backend
  - Basic **Grafana dashboard** for request rate, error rate, p95 latency
- **Tools I'll learn:** Google Generative AI SDK, OpenTelemetry, Grafana, structured logging
- **Time commitment:** 8–10 hours/week
- **Done looks like:** A student asks "Do I need a laptop for the AI Hackathon?" and gets an accurate answer citing the event's rules field. I can trace any request through the system in Grafana.

### Milestone 3 (Nov–Dec 2026): Multi-Tenancy + Security Hardening

- **What I'll add:**
  - **Row-level security** policies for club data isolation (PostgreSQL RLS or application-level tenant filtering)
  - Migrate JWT from `localStorage` to **HttpOnly cookies** with `SameSite=Strict`
  - Add **rate limiting** middleware (slowapi or custom)
  - Add **Alembic migration** as a CI/CD step before deployment
- **Tools I'll learn:** PostgreSQL RLS, cookie-based auth, rate limiting patterns, migration CI/CD
- **Time commitment:** 6–8 hours/week
- **Done looks like:** A penetration test (OWASP ZAP) shows no critical vulnerabilities. Club A's admin cannot access Club B's data even with a crafted request.

---

## 3rd Year Internship Plan (Jun–Jul 2027)

This project becomes the foundation for **F1 (Multi-Tenant SaaS Platform)** or **F2 (Event-Driven Architecture)** in the 3rd-year internship problem statements. The multi-tenancy work (Milestone 3) directly maps to F1's isolation requirements. The async email pipeline and observability work (Milestones 1–2) map to F2's event-driven patterns. I will target backend/platform engineering roles at Razorpay, Cred, or Groww, where the "I built a multi-tenant platform with observability and GitOps" narrative is directly relevant.

## What I'll need from the placement / mentor ecosystem

- A mentor experienced with Kubernetes and Helm charts (for the AKS migration)
- Access to Azure free-tier credits for AKS (or a local Kind cluster for development)
- The 3rd-year cohort's Slack channel for peer learning on observability patterns
- 2–3 mock interviews where I present EventHub's architecture and defend my ADR decisions

## Risks & open questions

| Risk | Mitigation |
|:-----|:-----------|
| AKS exceeds free tier (costs money) | Use Kind (Kubernetes in Docker) locally for development. Only deploy to AKS for the final demo. |
| Gemini API rate limits (free tier: 60 RPM) | Implement response caching for common questions. Fall back to rule-based answers when rate-limited. |
| Semester workload (Aug–Dec is heavy) | Cap at 8 hours/week. If a milestone slips, it slips. Consistency > velocity. |
| Alembic migration breaks production | Always run migrations against a staging Neon branch before production. Neon supports database branching for free. |
| Scope creep (adding React, adding mobile) | The frontend stays Vanilla JS. The value is in backend depth, not frontend breadth. |
