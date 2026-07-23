import os , time , gc
from datetime import datetime, timedelta, timezone
from pathlib import Path


TEST_DB_PATH = (Path(__file__).parent / "test_eventhub.db").resolve()

os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["ALGORITHM"] = "HS256"
os.environ["ACS_CONNECTION_STRING"] = "endpoint=https://test.communication.azure.com/;accesskey=dGVzdA=="
os.environ["SENDER_EMAIL"] = "DoNotReply@test.com"
os.environ["ALLOWED_ORIGINS"] = "*"
os.environ["GEMINI_API_KEY"] = ""
os.environ["GEMINI_MODEL"] = "test-model"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.database import Base, get_db
from app.main import app
import app.main as main_module
from app import models


engine = create_engine(
    f"sqlite:///{TEST_DB_PATH}",
    connect_args={"check_same_thread": False},
    poolclass=NullPool,
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def delete_test_db(max_retries: int = 5) -> bool:
    for _ in range(max_retries):
        try:
            if TEST_DB_PATH.exists():
                TEST_DB_PATH.unlink()
            return True
        except PermissionError:
            time.sleep(0.5)  # Wait half a second and try again
        except FileNotFoundError:
            return True
    
    print(f"\nWarning: Could not delete {TEST_DB_PATH} due to lingering file locks.")
    return False





@pytest.fixture(scope="session", autouse=True)
def create_tables():
    # 1. Setup
    Base.metadata.create_all(bind=engine)
    
    yield  # Tests run here
    
    # 2. Teardown
    Base.metadata.drop_all(bind=engine)
    # Force garbage collection to destroy any unclosed dangling test sessions
    gc.collect() 
    # 3. Dispose the test engine we created in this file
    engine.dispose()
    # 4. Dispose the MAIN app's engine that was created during imports
    try:
        from app.database import engine as app_engine
        app_engine.dispose()
    except ImportError:
        pass # If your engine is named differently in app.database, adjust the import
    
    # 5. Delete the database safely
    delete_test_db()


@pytest.fixture(autouse=True)
def clean_tables():
    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())
    yield


@pytest.fixture(autouse=True)
def disable_emails(monkeypatch):
    monkeypatch.setattr(
        main_module,
        "send_email_stub",
        lambda *args, **kwargs: None,
    )


@pytest.fixture
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def register_user(client, db):
    def _register(
        email,
        password="password123",
        name="Test User",
        role="student",
    ):
        res = client.post(
            "/api/auth/register",
            json={
                "email": email,
                "password": password,
                "name": name,
                "role": role,
            },
        )

        assert res.status_code == 200, res.text

        otp = (
            db.query(models.OTP)
            .filter(models.OTP.email == email)
            .order_by(models.OTP.id.desc())
            .first()
        )

        assert otp is not None, "OTP record was not created"

        verify = client.post(
            "/api/auth/verify-otp",
            json={
                "email": email,
                "otp": otp.code,
            },
        )

        assert verify.status_code == 200, verify.text

        return verify.json()["access_token"]

    return _register


@pytest.fixture
def auth_header(register_user):
    def _auth(role="student", email=None, name=None):
        email = email or f"{role}@test.com"
        name = name or role.capitalize()

        token = register_user(
            email=email,
            role=role,
            name=name,
        )

        return {"Authorization": f"Bearer {token}"}

    return _auth


@pytest.fixture
def coordinator_headers(auth_header):
    return auth_header(
        role="coordinator",
        email="coordinator@test.com",
        name="Coordinator",
    )


@pytest.fixture
def create_club(client, coordinator_headers):
    def _create(name="Tech Club"):
        res = client.post(
            "/api/clubs",
            json={"name": name},
            headers=coordinator_headers,
        )

        assert res.status_code == 200, res.text

        return res.json()["id"]

    return _create


@pytest.fixture
def admin_setup(client, register_user, coordinator_headers, create_club):
    admin_email = "admin@test.com"

    admin_token = register_user(
        email=admin_email,
        role="admin",
        name="Club Admin",
    )

    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    club_id = create_club("Tech Club")

    assign = client.post(
        f"/api/clubs/{club_id}/assign-admin",
        params={"admin_email": admin_email},
        headers=coordinator_headers,
    )

    assert assign.status_code == 200, assign.text

    return admin_headers, club_id, admin_email


@pytest.fixture
def future_time():
    return (datetime.now(timezone.utc) + timedelta(hours=4)).isoformat()


@pytest.fixture
def event_payload():
    def _payload(club_id, title="Test Event", start_time=None):
        if not start_time:
            # --- CHANGE THIS LINE ---
            # Update the default time to be 1 day in the future 
            # so it easily clears the 3-hour backend guardrail.
            start_time = (datetime.now() + timedelta(days=1)).isoformat()
            # ------------------------
            
        return {
            "title": title,
            "club_id": club_id,
            "start_time": start_time,
            "description": "Test description",
            "rules": "Test rules",
            "is_featured": False
        }
    return _payload


@pytest.fixture
def create_event(client, event_payload):
    def _create(admin_headers, club_id, title="Test Event", start_time=None):
        res = client.post(
            "/api/admin/events",
            json=event_payload(
                club_id=club_id,
                title=title,
                start_time=start_time,
            ),
            headers=admin_headers,
        )

        assert res.status_code == 200, res.text

        return res.json()["event_id"]

    return _create