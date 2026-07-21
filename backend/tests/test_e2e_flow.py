def test_full_event_lifecycle_e2e(
    client,
    register_user,
    coordinator_headers,
    create_club,
    create_event,
):
    # Coordinator creates club
    club_id = create_club("E2E Club")

    # Admin registers
    admin_token = register_user(
        email="admin-e2e@test.com",
        role="admin",
        name="E2E Admin",
    )

    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Coordinator assigns admin to club
    assign = client.post(
        f"/api/clubs/{club_id}/assign-admin",
        params={"admin_email": "admin-e2e@test.com"},
        headers=coordinator_headers,
    )

    assert assign.status_code == 200

    # Admin creates event
    event_id = create_event(
        admin_headers,
        club_id,
        title="E2E Event",
    )

    # Student registers
    student_token = register_user(
        email="student-e2e@test.com",
        role="student",
        name="E2E Student",
    )

    student_headers = {"Authorization": f"Bearer {student_token}"}

    # Student joins club
    join = client.post(
        f"/api/clubs/{club_id}/join",
        headers=student_headers,
    )

    assert join.status_code == 200

    # Student sees upcoming events
    events = client.get(
        "/api/events/upcoming",
        headers=student_headers,
    )

    assert events.status_code == 200

    event_ids = [e["id"] for e in events.json()]
    assert event_id in event_ids

    # Student RSVPs
    rsvp = client.post(
        f"/api/events/{event_id}/rsvp",
        headers=student_headers,
    )

    assert rsvp.status_code == 200

    # Admin sees RSVPs
    rsvps = client.get(
        f"/api/admin/events/{event_id}/rsvps",
        headers=admin_headers,
    )

    assert rsvps.status_code == 200

    rsvp_id = rsvps.json()[0]["rsvp_id"]

    # Admin marks attendance
    mark = client.post(
        f"/api/admin/events/{event_id}/attendance",
        json={
            "rsvp_id": rsvp_id,
            "is_present": True,
        },
        headers=admin_headers,
    )

    assert mark.status_code == 200

    # Admin submits attendance
    submit = client.post(
        f"/api/admin/events/{event_id}/submit-attendance",
        headers=admin_headers,
    )

    assert submit.status_code == 200

    # Coordinator sees reports
    reports = client.get(
        "/api/coordinator/reports",
        headers=coordinator_headers,
    )

    assert reports.status_code == 200
    assert reports.json()["total_rsvps"] >= 1