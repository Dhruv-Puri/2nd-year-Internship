from datetime import datetime, timedelta, timezone


def test_student_cannot_create_event(
    client,
    auth_header,
    create_club,
    event_payload,
):
    club_id = create_club()
    student_headers = auth_header("student")

    res = client.post(
        "/api/admin/events",
        json=event_payload(club_id),
        headers=student_headers,
    )

    assert res.status_code == 403


def test_admin_cannot_create_event_for_unassigned_club(
    client,
    admin_setup,
    create_club,
    event_payload,
):
    admin_headers, _, _ = admin_setup

    other_club_id = create_club("Lit Club")

    res = client.post(
        "/api/admin/events",
        json=event_payload(other_club_id),
        headers=admin_headers,
    )

    assert res.status_code == 403


def test_admin_event_must_start_at_least_3_hours_ahead(
    client,
    admin_setup,
    event_payload,
):
    admin_headers, club_id, _ = admin_setup

    soon = (datetime.now(timezone.utc) + timedelta(minutes=30)).isoformat()

    res = client.post(
        "/api/admin/events",
        json=event_payload(club_id, start_time=soon),
        headers=admin_headers,
    )

    assert res.status_code == 400


def test_admin_can_create_event(
    client,
    admin_setup,
    create_event,
):
    admin_headers, club_id, _ = admin_setup

    event_id = create_event(admin_headers, club_id)

    assert isinstance(event_id, int)