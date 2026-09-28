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
