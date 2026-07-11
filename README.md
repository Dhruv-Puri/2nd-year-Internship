# 🎟️ EventHub: Internal Tool Backbone + AI RAG Extension

> *A centralized, cloud-native platform for university student clubs to organize events, manage RSVPs, and query event guidelines using an integrated AI assistant.*


**Author:** Dhruv  
**Segment:** Segment 4 — Foundations of Cloud & DevOps  
**Problem Statement Code:** J2 (Internal Tool Backbone)  

---

## 🧠 What I Learned

### Week 2
* **Pydantic & ORM Integration:** I was genuinely surprised by how elegantly Pydantic bridges the gap with SQLAlchemy using `ConfigDict(from_attributes=True)` to dictate how data flows between different modules. It automatically reads ORM object attributes and validates them, saving immense boilerplate code.
* **Azure Infrastructure & Network Boundaries:** Gained deep insight into how Azure handles infrastructure by cleanly decoupling frontend and backend deployments. It was eye-opening to see how strictly cloud network boundaries are enforced, reinforcing the importance of isolating database URLs and secret keys in the `.env` pipeline.
* **SQLAlchemy Relationships & State Sync:** Learned to establish robust SQLAlchemy relationships to handle state management across entities.
* **Temporal Guardrails & Validation:** Added strict backend guardrails, such as enforcing a 3-hour minimum buffer from the current time for admins creating or updating events, and preventing RSVPs to past events.
* **UI Abstraction & Role-Based State:** Developed an `authFetch` wrapper function in JavaScript that automatically injects the authentication token into requests, streamlining the logic to display three distinct dashboard panels (Student, Admin, and Coordinator).

### Week 1
* **Decoupling Data Validation from Database Schema:** I gained a clear understanding of the architectural boundary in FastAPI between SQLAlchemy ORM models (which dictate the physical database table structure) and Pydantic schemas (which enforce strict data validation and API payload serialization).
* **Cross-Origin Resource Sharing (CORS):** I learned how to configure CORS middleware to allow cross-origin network requests. This was a critical step in establishing a fully decoupled architecture, enabling my standalone HTML/Vanilla JS frontend to securely communicate with the FastAPI backend.
* **Stateless Authentication (JWT & Bcrypt):** I built a secure, token-based authentication flow from scratch. This involved securely hashing user passwords using Bcrypt before saving them to PostgreSQL, and generating JSON Web Tokens (JWT) to authorize protected API endpoints statelessly.
* **Client-Side State & Route Management:** I learned how to manipulate the browser's history stack using JavaScript's `window.location.replace()`. This prevents authenticated users from navigating back to the login or registration pages via the browser's back button, preserving UX integrity.
* **Environment Isolation & Security:** I established best practices for handling sensitive credentials by abstracting database URLs, hashing algorithms, and JWT secret keys into `.env` files, ensuring they are strictly ignored by version control to prevent credential leakage.
* **Token Storage Mechanics:** I gained practical experience handling authentication state on the frontend by securely capturing JWTs from backend responses and storing them in `localStorage` to persist user sessions across page reloads.

---
## 🛠️ Tech Stack Justification

| Component | Choice | Why (one line) |
| :--- | :--- | :--- |
| **Frontend UI** | HTML / CSS / Vanilla JS | Zero-dependency, lightweight static assets optimized for fast edge delivery via Azure. |
| **Backend API** | FastAPI (Python) | High-throughput asynchronous framework with native Pydantic data validation. |
| **Database** | PostgreSQL | Robust relational engine for enforcing strict constraints across Users, Events, and RSVPs. |
| **Auth Layer** | JWT + Bcrypt | Secure, stateless token-based authentication paired with industry-standard cryptographic hashing. |
| **AI/RAG Engine** | HuggingFace Spaces | Dedicated microservice environment to prevent ML inference from blocking core API threads. |
| **Cloud Hosting** | Azure (App Service + Static Web Apps) | Platform-as-a-Service (PaaS) deployment that cleanly decouples frontend and backend infrastructure. |

#### Also planning to keep the JWT in `localStorage` for the final Azure deployment, or are you considering migrating it to `HttpOnly` cookies for enhanced XSS protection before the final week
---


## Note: rest of the details are added in the github issue and doc/ADR_001.md)
