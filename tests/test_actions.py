"""Tests for GDPR generation and action helpers."""

from cleanslate.core.models import GDPRRequestPayload
from cleanslate.core.actions import generate_gdpr_deletion_request


def test_gdpr_generation_italian():
    payload = GDPRRequestPayload(
        user_name="Pietro Rossi",
        user_email="pietro@example.com",
        service_name="Spotify",
        dpo_email="privacy@spotify.com",
        language="it",
    )
    res = generate_gdpr_deletion_request(payload)
    assert res["dpo_email"] == "privacy@spotify.com"
    assert "Art. 17 GDPR" in res["subject"]
    assert "Pietro Rossi" in res["body"]
    assert "DIRITTO ALLA CANCELLAZIONE" in res["body"]
    assert res["mailto_uri"].startswith("mailto:privacy@spotify.com")


def test_gdpr_generation_english():
    payload = GDPRRequestPayload(
        user_name="John Doe",
        user_email="john@example.com",
        service_name="Canva",
        dpo_email="privacy@canva.com",
        language="en",
    )
    res = generate_gdpr_deletion_request(payload)
    assert "Right to Erasure" in res["body"]
    assert "John Doe" in res["body"]
    assert "privacy@canva.com" in res["mailto_uri"]
