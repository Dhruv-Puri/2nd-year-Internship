def test_coordinator_can_create_club_assign_admin_and_read_reports(
    client,
    register_user,
    coordinator_headers,
):
    club = client.post(
        "/api/clubs",
        json={"name": "Tech Club"},
        headers=coordinator_headers,
    )

    assert club.status_code == 200

    club_id = club.json()["id"]

    register_user(
        email="admin@test.com",
        role="admin",
        name="Admin",
    )

    assign = client.post(
        f"/api/clubs/{club_id}/assign-admin",
        params={"admin_email": "admin@test.com"},
        headers=coordinator_headers,
    )

    assert assign.status_code == 200

    reports = client.get(
        "/api/coordinator/reports",
        headers=coordinator_headers,
    )

    assert reports.status_code == 200

    body = reports.json()

    expected_keys = [
        "events_per_club",
        "attendance_rate",
        "top_events",
        "total_rsvps",
        "active_events",
        "completed_events",
    ]

    for key in expected_keys:
        assert key in body


def test_student_cannot_access_coordinator_reports(
    client,
    auth_header,
):
    student_headers = auth_header("student")

    res = client.get(
        "/api/coordinator/reports",
        headers=student_headers,
    )

    assert res.status_code == 403