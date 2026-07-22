# Resume Bullets — EventHub (J2: Internal Tool Backbone)

**Author:** Dhruv Puri
**Date:** 25 July 2026

---

## Polished Bullets (Action Verb + Tech + Outcome)

1. **Architected and deployed a cloud-native event management platform** (FastAPI, PostgreSQL, Azure App Service) serving 3 role-based dashboards across 34 REST endpoints, with automated CI/CD via GitHub Actions (PyTest → Docker build → smoke test → GHCR push → Azure deploy) achieving zero-downtime container deployments.

2. **Designed a three-layer email guardrail system** using Azure Communication Services with a database-backed daily quota (10 emails/day), global toggle switch, and graceful exception handling — enabling safe demo environments while delivering real transactional emails (OTP, RSVP confirmations, attendance receipts) to user inboxes.

3. **Implemented a decoupled, zero-dependency frontend** (Vanilla JS, ~50KB total) with a runtime `config.js` injection pattern enabling identical behaviour across local Docker Compose and Azure Storage Static Website production environments, reducing reviewer onboarding from 10+ minutes to under 2 minutes.

---

## Usage Notes

- Use bullet 1 for **backend/DevOps roles** (emphasises architecture + CI/CD + deployment)
- Use bullet 2 for **platform engineering roles** (emphasises guardrail design + abuse prevention + cloud integration)
- Use bullet 3 for **full-stack roles** (emphasises frontend engineering + environment portability + DX)
- All three together tell the story: "I designed the system, I protected it, I made it deployable."
