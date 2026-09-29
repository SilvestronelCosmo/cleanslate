"""Tests for CleanSlate service directory and domain normalization."""

from cleanslate.core.directory import normalize_domain, lookup_service
from cleanslate.core.models import DeletionDifficulty


def test_normalize_domain():
    assert normalize_domain("user@spotify.com") == "spotify.com"
    assert normalize_domain("https://accounts.google.com/signin") == "google.com"
    assert normalize_domain("notifications.netflix.com") == "netflix.com"
    assert normalize_domain("amazon.it") == "amazon.it"


def test_lookup_service():
    spotify = lookup_service("spotify.com")
    assert spotify is not None
    assert spotify["name"] == "Spotify"
    assert spotify["difficulty"] == DeletionDifficulty.EASY
    assert "privacy@spotify.com" == spotify["dpo_email"]

    github = lookup_service("support@github.com")
    assert github is not None
    assert github["name"] == "GitHub"

    # Fuzzy name lookup
    adobe = lookup_service("Adobe")
    assert adobe is not None
    assert adobe["difficulty"] == DeletionDifficulty.HARD


def test_lookup_no_substring_false_positive():
    assert lookup_service("ix.com") is None
    assert lookup_service("a") is None
    netflix = lookup_service("mailer.netflix.com")
    assert netflix is not None
    assert netflix["name"] == "Netflix"
