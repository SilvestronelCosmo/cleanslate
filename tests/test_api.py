"""Tests for FastAPI endpoints using TestClient."""

from fastapi.testclient import TestClient
import importlib
from unittest.mock import Mock
import pytest

from cleanslate.web.app import app
from cleanslate.core.models import ScanSummary

webapp = importlib.import_module("cleanslate.web.app")

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
        return [], [{"domain": "discord.com", "cause": "rateLimit=True restituito dal modulo Holehe", "hint": "Captcha possibile"}]

    monkeypatch.setattr("cleanslate.web.app.run_osint_scan", mock_scan)
    response = client.post("/api/scan/osint", json={"email": "test@example.com"})
    assert response.status_code == 200
    data = response.json()
    assert data["unverified"] == ["discord.com"]
    assert len(data["unverified_details"]) == 1
    assert data["unverified_details"][0]["domain"] == "discord.com"
    assert data["unverified_details"][0]["cause"] == "rateLimit=True restituito dal modulo Holehe"
    assert data["unverified_details"][0]["hint"] == "Captcha possibile"


def test_unsubscribe_rejects_non_http():
    response = client.post(
        "/api/actions/unsubscribe",
        json={"unsub_url": "javascript:alert(1)"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False


@pytest.fixture
def saved_imap_profile(monkeypatch):
    profile = {"name": "user@example.com@imap.example.com:1993", "host": "imap.example.com", "port": 1993, "username": "user@example.com"}
    monkeypatch.setattr(webapp, "load_profile", Mock(return_value=profile), raising=False)
    password_reader = Mock(return_value="fake-secret")
    scanner = Mock(return_value=ScanSummary(target_email=profile["username"]))
    monkeypatch.setattr(webapp, "get_password", password_reader)
    monkeypatch.setattr(webapp, "scan_imap_inbox", scanner)
    return profile, password_reader, scanner


def test_imap_scan_profile_uses_saved_host_and_user(saved_imap_profile):
    profile, password_reader, scanner = saved_imap_profile
    response = client.post("/api/scan/imap", json={"profile_name": profile["name"]})
    assert response.status_code == 200
    password_reader.assert_called_once_with(profile["name"])
    scanner.assert_called_once_with(host=profile["host"], port=profile["port"], username=profile["username"], password="fake-secret", max_emails=150)
    assert "fake-secret" not in response.text


@pytest.mark.parametrize("field,value", [("host", "other.example.com"), ("port", 993), ("username", "other@example.com")])
def test_imap_scan_profile_rejects_mismatched_host(saved_imap_profile, field, value):
    profile, password_reader, scanner = saved_imap_profile
    response = client.post("/api/scan/imap", json={**profile, "profile_name": profile["name"], field: value})
    assert response.status_code == 400
    password_reader.assert_not_called()
    scanner.assert_not_called()


def test_imap_scan_unknown_profile_404(saved_imap_profile, monkeypatch):
    _, password_reader, scanner = saved_imap_profile
    monkeypatch.setattr(webapp, "load_profile", Mock(return_value=None))
    response = client.post("/api/scan/imap", json={"profile_name": "unknown"})
    assert response.status_code == 404
    password_reader.assert_not_called()
    scanner.assert_not_called()


@pytest.fixture
def imap_store(tmp_path, monkeypatch):
    from cleanslate.core import keychain
    from keyring.backends import macOS
    import subprocess
    monkeypatch.setattr(subprocess, "run", Mock(side_effect=AssertionError("Subprocess forbidden")))
    monkeypatch.setattr(keychain, "CONFIG_DIR", str(tmp_path))
    monkeypatch.setattr(keychain, "CONFIG_FILE", str(tmp_path / "profiles.json"))
    monkeypatch.setattr(keychain, "platform", "darwin", raising=False)
    backend = Mock()
    backend.get_password.return_value = None
    monkeypatch.setattr(macOS, "Keyring", Mock(return_value=backend))
    return backend


def test_imap_profiles_response_has_no_password(imap_store, caplog):
    payload = {"name": "ignored-label", "host": "imap.example.com", "username": "user@example.com", "password": "fake-secret"}
    saved = client.post("/api/imap/profiles", json=payload)
    assert saved.status_code == 200
    assert saved.json()["profile_name"] == "user@example.com@imap.example.com:993"
    listed = client.get("/api/imap/profiles")
    assert listed.status_code == 200
    assert set(listed.json()[0]) == {"name", "host", "port", "username"}
    assert "fake-secret" not in saved.text + listed.text + caplog.text


def test_imap_delete_error_returns_generic_500_and_keeps_profile(imap_store, caplog):
    from cleanslate.core import keychain
    name = keychain.save_profile("imap.example.com", 993, "user@example.com", "fake-secret")
    imap_store.delete_password.side_effect = RuntimeError("denied: fake-secret")
    response = client.delete(f"/api/imap/profiles/{name}")
    assert response.status_code == 500
    assert "fake-secret" not in response.text + caplog.text
    assert keychain.load_profile(name) is not None


def test_imap_save_error_has_no_password(imap_store, caplog):
    imap_store.set_password.side_effect = RuntimeError("denied: fake-secret")
    response = client.post("/api/imap/profiles", json={"host": "imap.example.com", "username": "user@example.com", "password": "fake-secret"})
    assert response.status_code == 500
    assert "fake-secret" not in response.text + caplog.text


@pytest.mark.parametrize("operation,status", [("keychain", 500), ("scan", 400)])
def test_imap_scan_errors_have_no_password(saved_imap_profile, operation, status, caplog):
    profile, password_reader, scanner = saved_imap_profile
    failing = password_reader if operation == "keychain" else scanner
    failing.side_effect = RuntimeError("failed: fake-secret")
    response = client.post("/api/scan/imap", json={"profile_name": profile["name"]})
    assert response.status_code == status
    assert "fake-secret" not in response.text + caplog.text


@pytest.mark.parametrize("path", ["/api/scan/imap", "/api/imap/profiles"])
def test_imap_validation_errors_have_no_password(path, caplog):
    response = client.post(path, json={"host": "imap.example.com", "username": "user@example.com", "password": {"invalid": "fake-secret"}})
    assert response.status_code == 422
    assert "fake-secret" not in response.text + caplog.text


def test_imap_manual_scan_without_profile(saved_imap_profile):
    _, password_reader, scanner = saved_imap_profile
    response = client.post("/api/scan/imap", json={"host": "manual.example.com", "username": "manual@example.com", "password": "manual-secret"})
    assert response.status_code == 200
    password_reader.assert_not_called()
    assert scanner.call_args.kwargs["host"] == "manual.example.com"
    assert scanner.call_args.kwargs["password"] == "manual-secret"
