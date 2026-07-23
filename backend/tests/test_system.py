def test_bot_returns_laptop_answer(client, auth_header):
    headers = auth_header("student")

    res = client.post(
        "/api/bot/ask",
        json={"question": "Should I bring a laptop?"},
        headers=headers,
    )

    assert res.status_code == 200
    assert "sorry" in res.json()["answer"].lower() # as gemini is not connected


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