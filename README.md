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
* **Stateless Authentication (JWT & Bcrypt):** I built a secure, token-based authentication flow from scratch. This involved securely hashing user passwords using Bcrypt before saving them to Azure SQL, and generating JSON Web Tokens (JWT) to authorize protected API endpoints statelessly.
* **Client-Side State & Route Management:** I learned how to manipulate the browser's history stack using JavaScript's `window.location.replace()`. This prevents authenticated users from navigating back to the login or registration pages via the browser's back button, preserving UX integrity.
* **Environment Isolation & Security:** I established best practices for handling sensitive credentials by abstracting database URLs, hashing algorithms, and JWT secret keys into `.env` files, ensuring they are strictly ignored by version control to prevent credential leakage.
* **Token Storage Mechanics:** I gained practical experience handling authentication state on the frontend by securely capturing JWTs from backend responses and storing them in `localStorage` to persist user sessions across page reloads.

---
## 🛠️ Tech Stack Justification

| Component | Choice | Why (one line) |
| :--- | :--- | :--- |
| **Frontend UI** | HTML / CSS / Vanilla JS | Zero-dependency, lightweight static assets optimized for fast edge delivery via Azure. |
| **Backend API** | FastAPI (Python) | High-throughput asynchronous framework with native Pydantic data validation. |
| **Database** | Azure SQL | Robust relational engine for enforcing strict constraints across Users, Events, and RSVPs. |
| **Auth Layer** | JWT + Bcrypt | Secure, stateless token-based authentication paired with industry-standard cryptographic hashing. |
| **AI/RAG Engine** | HuggingFace Spaces | Dedicated microservice environment to prevent ML inference from blocking core API threads. |
| **Cloud Hosting** | Azure (Web App Service +  Static Storage Account) | Platform-as-a-Service (PaaS) deployment that cleanly decouples frontend and backend infrastructure. |


## 🏗️ Architecture Diagram
```mermaid
graph TD
    User((User Browser))
    subgraph Azure Frontend
        SWA[Azure Storage Account<br/>Static Website Hosting<br/>HTML/CSS/JS]
    end
    subgraph Azure Backend
        API[Azure App Service<br/>FastAPI Container]
    end
    subgraph Azure Data & Services
        DB[(Azure Database<br/>for Azure SQL)]
        ACS[Azure Communication<br/>Services]
    end

    User -->|Requests UI| SWA
    User -->|REST / Bearer JWT| API
    API -->|Read/Write Data| DB
    API -->|Send OTPs & Reminders| ACS
```

---
## 🚀 Quickstart
---
A reviewer must be able to go from `git clone` to running product in < 20 minutes.

### Prerequisites
- Python 3.11+
- Docker & Docker Compose (Optional, for containerized testing)

### Install
```bash
# 1. Clone the repository
git clone <your-repo-url>
cd eventhub

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

### Configure Environment
Create a `.env` file in the root directory based on `.env.example`:
```env
DATABASE_URL="postgresql://user:password@localhost:5432/eventhub"
SECRET_KEY="your-super-secret-jwt-key"
ALGORITHM="HS256"
ACS_CONNECTION_STRING="your-azure-communication-services-connection-string"
SENDER_EMAIL="your-verified-azure-sender-email"
```

### Run
```bash
# Start the FastAPI server
uvicorn backend.app.main:app --reload
```
*The API will be available at `http://127.0.0.1:8000`. Open `frontend/index.html` in your browser (via Live Server) to interact with the UI.*

### Test
```bash
# Run the pytest suite to validate backend guardrails and auth flows
pytest
```

## 📊 Data Sources
The application uses synthetic seed data generated automatically on startup (`seed_data` function in `main.py`) to populate initial Clubs and Events for immediate testing and demonstration purposes.

## 📂 Architecture Decision Records (ADRs)
All major architectural choices are documented in the `/docs` directory:
- [ADR-001: Decoupled Vanilla JS Frontend with JWT LocalStorage](./docs/ADR-001.md)
- [ADR-002: Unified Azure PaaS Ecosystem for Full-Stack Hosting](./docs/ADR-002.md)
- [ADR-003: Azure Communication Services (ACS) for Transactional Emails](./docs/ADR-003.md)

## ✨ Mini-Extension: Automated Notification Pipeline
For the Week 3 Mini-Extension, I moved beyond simple "stubbed" console logs and integrated a real, production-grade transactional email pipeline using **Azure Communication Services (ACS)**. 
- **Automated Workflows:** Sends real emails for RSVP confirmations, Attendance Finalization receipts, and cron-triggerable 24-hour reminder blasts.
- **OTP Security:** Reused the ACS infrastructure to build a secure, time-bound OTP verification flow for new user registrations and password resets.
- **Abuse Prevention:** Engineered an `EmailQuota` database model that hard-limits the system to 10 emails per day, alongside a global frontend toggle switch to instantly enable/disable the email pipeline for demo environments.

## ⚠️ Known Limitations
1. **XSS Vulnerability Surface:** JWTs are currently stored in `localStorage` for ease of cross-origin decoupled testing. In a production environment, these should be migrated to `HttpOnly` cookies.
2. **Synchronous Email Sending:** The Azure ACS API calls are currently synchronous. In a production system, these should be offloaded to FastAPI `BackgroundTasks` or an Azure Service Bus queue to prevent blocking the main API thread.
3. **No Schema Migrations:** Database tables are currently created using `Base.metadata.create_all()`. For production, Alembic should be integrated to handle safe, version-controlled schema migrations.

## 🔮 What I'd Do in 3rd Year
This project serves as the foundational seed for my 3rd-year portfolio. Next year, I plan to:
- Implement multi-tenancy to isolate club data securely.
- Replace the basic `/api/bot/ask` endpoint with a full Retrieval-Augmented Generation (RAG) pipeline using Azure AI Search and LangChain to allow students to "chat" with event rulebooks.
- Migrate from manual Docker deployments to a fully automated GitOps CI/CD pipeline using GitHub Actions and Azure Kubernetes Service (AKS).
*(See `docs/roadmap_3rd_year.md` for the detailed 12-month plan).*

## 📜 License & Acknowledgements
- **License:** MIT License
- **Acknowledgements:** Built as part of the 2nd Year B.Tech CSE-AIDE Internship Program (Foundations of Cloud & DevOps). Special thanks to my segment mentor for guidance on Azure PaaS networking and API guardrails.
```

