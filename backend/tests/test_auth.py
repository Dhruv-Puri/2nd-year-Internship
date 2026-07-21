from app import models

def test_openapi_lists_at_least_10_endpoints(client):
    res = client.get("/openapi.json")

    assert res.status_code == 200
    assert len(res.json()["paths"]) >= 10


def test_register_verify_login_and_me(client, register_user):
    token = register_user("student@test.com")

    me = client.get(
        "/api/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert me.status_code == 200
    assert me.json()["email"] == "student@test.com"

    login = client.post(
        "/api/auth/login",
        json={
            "email": "student@test.com",
            "password": "password123",
        },
    )

    assert login.status_code == 200
    assert "access_token" in login.json()


def test_login_wrong_password(client, register_user):
    register_user("student@test.com")

    res = client.post(
        "/api/auth/login",
        json={
            "email": "student@test.com",
            "password": "wrong-password",
        },
    )

    assert res.status_code == 401


def test_duplicate_registration_blocked(client, register_user):
    register_user("student@test.com")

    res = client.post(
        "/api/auth/register",
        json={
            "email": "student@test.com",
            "password": "password123",
            "name": "Duplicate User",
            "role": "student",
        },
    )

    assert res.status_code == 400


def test_protected_route_requires_token(client):
    res = client.get("/api/users/me")

    assert res.status_code == 401


def test_forgot_password_flow(client, register_user, db):
    register_user("forgot@test.com")

    res = client.post(
        "/api/auth/forgot-password",
        params={"email": "forgot@test.com"},
    )

    assert res.status_code == 200

    otp = (
        db.query(models.OTP)
        .filter(models.OTP.email == "forgot@test.com")
        .order_by(models.OTP.id.desc())
        .first()
    )

    assert otp is not None

    reset = client.post(
        "/api/auth/reset-password",
        json={
            "email": "forgot@test.com",
            "otp": otp.code,
            "new_password": "newpassword123",
        },
    )

    assert reset.status_code == 200

    login = client.post(
        "/api/auth/login",
        json={
            "email": "forgot@test.com",
            "password": "newpassword123",
        },
    )

    assert login.status_code == 200