def test_bot_returns_laptop_answer(client):
    res = client.post(
        "/api/bot/ask",
        json={"question": "Should I bring a laptop?"},
    )

    assert res.status_code == 200
    assert "laptop" in res.json()["answer"].lower()


def test_email_toggle_endpoint(client):
    res = client.put(
        "/api/system/toggle-email",
        params={"toggle": False},
    )

    assert res.status_code == 200
    assert res.json()["Email Recieving Status"] is False


def test_send_reminders_endpoint_runs(client):
    res = client.post("/api/system/send-reminders")

    assert res.status_code == 200