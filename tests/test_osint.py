"""Unit tests for OSINT probing and module deduplication."""


import importlib
import pytest

from cleanslate.core.osint import HOLEHE_MODULES, OSINT_SERVICE_NAMES, run_osint_scan
from cleanslate.core.models import ServiceEntry, ServiceCategory, DeletionDifficulty


def test_holehe_modules_importable():
    count = 0
    for mod_path in HOLEHE_MODULES:
        full_name = mod_path if mod_path.startswith("holehe.modules.") else f"holehe.modules.{mod_path}"
        mod = importlib.import_module(full_name)
        short = mod_path.split(".")[-1]
        assert hasattr(mod, short)
        count += 1
    assert count == 14


def test_osint_service_names_count():
    assert len(OSINT_SERVICE_NAMES) == 16


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_run_osint_scan_maps_and_dedupes(monkeypatch):
    github_entry = ServiceEntry(
        name="GitHub",
        domain="github.com",
        category=ServiceCategory.ACCOUNT,
        found_via="osint",
        difficulty=DeletionDifficulty.EASY,
    )

    async def mock_gravatar(client, email):
        return None

    async def mock_duolingo(client, email):
        return None

    async def mock_github(client, email):
        return github_entry

    async def mock_spotify(client, email):
        return None

    async def mock_holehe(email, client):
        return [
            {"name": "github", "domain": "github.com", "exists": True, "rateLimit": False},
            {"name": "twitter", "domain": "twitter.com", "exists": True, "rateLimit": False},
            {"name": "discord", "domain": "discord.com", "exists": False, "rateLimit": True},
            {"name": "strava", "domain": "strava.com", "exists": False, "rateLimit": False},
        ]

    monkeypatch.setattr("cleanslate.core.osint.check_gravatar", mock_gravatar)
    monkeypatch.setattr("cleanslate.core.osint.check_duolingo", mock_duolingo)
    monkeypatch.setattr("cleanslate.core.osint.check_github", mock_github)
    monkeypatch.setattr("cleanslate.core.osint.check_spotify", mock_spotify)
    monkeypatch.setattr("cleanslate.core.osint._run_holehe", mock_holehe)

    results, unverified = await run_osint_scan("test@example.com")
    domains = {s.domain for s in results}
    assert domains == {"github.com", "twitter.com"}
    assert len([s for s in results if s.domain == "github.com"]) == 1
    assert unverified == ["discord.com"]
