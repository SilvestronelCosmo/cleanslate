"""Tests for FastAPI endpoints using TestClient."""

from fastapi.testclient import TestClient
from cleanslate.web.app import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200


def test_directory_search():
    response = client.get("/api/directory?q=spotify")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["name"] == "Spotify"


def test_demo_data():
    response = client.get("/api/demo-data")
    assert response.status_code == 200
    data = response.json()
    assert data["total_services"] > 0
    assert any(s["name"] == "Spotify" for s in data["services"])
    assert any(s["name"] == "Substack" for s in data["services"])


def test_gdpr_template_api():
    payload = {
        "user_name": "Test User",
        "user_email": "test@domain.com",
        "service_name": "Netflix",
        "dpo_email": "privacy@netflix.com",
        "language": "it",
    }
    response = client.post("/api/actions/gdpr-template", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "privacy@netflix.com" in data["dpo_email"]
    assert "Art. 17" in data["subject"]


def test_no_cors_header():
    response = client.options(
        "/api/scan/osint",
        headers={
            "Origin": "https://evil.example",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert "access-control-allow-origin" not in response.headers


def test_mbox_upload_filename_traversal():
    mbox_content = (
        b"From user@example.com Mon Sep 28 12:00:00 2026\n"
        b"From: Spotify <no-reply@spotify.com>\n"
        b"Subject: Welcome to Spotify\n"
        b"Date: Mon, 28 Sep 2026 12:00:00 +0200\n\n"
        b"Content\n"
    )
    files = {"file": ("../../evil.mbox", mbox_content, "application/octet-stream")}
    response = client.post("/api/scan/mbox", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["target_email"] == "evil.mbox"
    assert data["total_services"] == 1


def test_osint_endpoint_reports_unverified(monkeypatch):
    async def mock_scan(email):
        return [], ["discord.com"]

    monkeypatch.setattr("cleanslate.web.app.run_osint_scan", mock_scan)
    response = client.post("/api/scan/osint", json={"email": "test@example.com"})
    assert response.status_code == 200
    data = response.json()
    assert data["unverified"] == ["discord.com"]


def test_unsubscribe_rejects_non_http():
    response = client.post(
        "/api/actions/unsubscribe",
        json={"unsub_url": "javascript:alert(1)"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
