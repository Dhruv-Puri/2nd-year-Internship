from datetime import datetime, timedelta, timezone


def test_student_can_join_club_see_event_and_rsvp(
    client,
    admin_setup,
    auth_header,
    create_event,
):
    admin_headers, club_id, _ = admin_setup

    event_id = create_event(
        admin_headers,
        club_id,
        title="RSVP Event",
    )

    student_headers = auth_header("student")

    join = client.post(
        f"/api/clubs/{club_id}/join",
        headers=student_headers,
    )

    assert join.status_code == 200

    events = client.get(
        "/api/events/upcoming",
        headers=student_headers,
    )

    assert events.status_code == 200

    event_ids = [e["id"] for e in events.json()]
    assert event_id in event_ids

    rsvp = client.post(
        f"/api/events/{event_id}/rsvp",
        headers=student_headers,
    )

    assert rsvp.status_code == 200

    duplicate = client.post(
        f"/api/events/{event_id}/rsvp",
        headers=student_headers,
    )

    assert duplicate.status_code == 400

    mine = client.get(
        "/api/users/me/rsvps",
        headers=student_headers,
    )

    assert mine.status_code == 200
    assert len(mine.json()) == 1

    cancel = client.delete(
        f"/api/events/{event_id}/rsvp",
        headers=student_headers,
    )

    assert cancel.status_code == 200


def test_attendance_submission_locks_event(
    client,
    admin_setup,
    auth_header,
    create_event,
    event_payload,
):
    admin_headers, club_id, _ = admin_setup

    event_id = create_event(
        admin_headers,
        club_id,
        title="Lock Event",
    )

    student_headers = auth_header("student")

    client.post(
        f"/api/clubs/{club_id}/join",
        headers=student_headers,
    )

    client.post(
        f"/api/events/{event_id}/rsvp",
        headers=student_headers,
    )

    rsvps = client.get(
        f"/api/admin/events/{event_id}/rsvps",
        headers=admin_headers,
    )

    assert rsvps.status_code == 200

    rsvp_id = rsvps.json()[0]["rsvp_id"]

    mark = client.post(
        f"/api/admin/events/{event_id}/attendance",
        json={
            "rsvp_id": rsvp_id,
            "is_present": True,
        },
        headers=admin_headers,
    )

    assert mark.status_code == 200

    submit = client.post(
        f"/api/admin/events/{event_id}/submit-attendance",
        headers=admin_headers,
    )

    assert submit.status_code == 200

    cancel = client.delete(
        f"/api/events/{event_id}/rsvp",
        headers=student_headers,
    )

    assert cancel.status_code == 400

    delete = client.delete(
        f"/api/admin/events/{event_id}",
        headers=admin_headers,
    )

    assert delete.status_code == 400

    update_payload = event_payload(
        club_id,
        title="Updated Event",
        start_time=(datetime.now(timezone.utc) + timedelta(hours=6)).isoformat(),
    )

    update = client.put(
        f"/api/admin/events/{event_id}",
        json=update_payload,
        headers=admin_headers,
    )

    assert update.status_code == 400