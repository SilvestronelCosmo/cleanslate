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
    assert count == 13


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
    assert len(unverified) == 1
    assert unverified[0]["domain"] == "discord.com"
    assert unverified[0]["cause"] == "rateLimit=True restituito dal modulo Holehe"


@pytest.mark.anyio
async def test_unverified_includes_separate_hint(monkeypatch):
    """Known explanations stay in hint; cause reports only the module flag."""

    async def mock_gravatar(client, email):
        return None

    async def mock_duolingo(client, email):
        return None

    async def mock_github(client, email):
        return None

    async def mock_spotify(client, email):
        return None

    async def mock_holehe(email, client):
        return [
            {"name": "pinterest", "domain": "pinterest.com", "exists": False, "rateLimit": True},
            {"name": "patreon", "domain": "patreon.com", "exists": False, "rateLimit": True},
        ]

    monkeypatch.setattr("cleanslate.core.osint.check_gravatar", mock_gravatar)
    monkeypatch.setattr("cleanslate.core.osint.check_duolingo", mock_duolingo)
    monkeypatch.setattr("cleanslate.core.osint.check_github", mock_github)
    monkeypatch.setattr("cleanslate.core.osint.check_spotify", mock_spotify)
    monkeypatch.setattr("cleanslate.core.osint._run_holehe", mock_holehe)

    results, unverified = await run_osint_scan("test@example.com")
    assert len(results) == 0
    assert len(unverified) == 2
    domains = {u["domain"] for u in unverified}
    assert domains == {"pinterest.com", "patreon.com"}
    for u in unverified:
        assert u["cause"] == "rateLimit=True restituito dal modulo Holehe"
        assert u["hint"] == osint.KNOWN_UNRELIABLE[u["domain"]]
        assert u["reason"] == u["cause"]


import asyncio
from types import SimpleNamespace
import httpx
from cleanslate.core import osint


NATIVE_CASES = [
    (osint.check_gravatar, 'gravatar.com', {'entry': []}, {'entry': [{'displayName': 'test'}]}),
    (osint.check_duolingo, 'duolingo.com', {'users': []}, {'users': [{'username': 'test'}]}),
    (osint.check_github, 'github.com', {'total_count': 0, 'items': []}, {'total_count': 1, 'items': [{'login': 'test'}]}),
    (osint.check_spotify, 'spotify.com', {'status': 1}, {'status': 20}),
]


def mock_scan_http(monkeypatch, response):
    async def get(self, url, **kwargs):
        if isinstance(response, Exception):
            raise response
        return response

    async def holehe(email, client):
        return []

    async def negative(client, email):
        return None

    monkeypatch.setattr(httpx.AsyncClient, 'get', get)
    monkeypatch.setattr(osint, '_run_holehe', holehe)
    for name in ('check_gravatar', 'check_duolingo', 'check_spotify'):
        monkeypatch.setattr(osint, name, negative)


@pytest.mark.anyio
@pytest.mark.parametrize('status,headers,cause', [
    (403, {}, 'HTTP 403'),
    (403, {'x-ratelimit-remaining': '0'}, 'HTTP 403 (limite di richieste)'),
    (429, {}, 'HTTP 429 (limite di richieste)'),
])
async def test_github_403_is_unverified(monkeypatch, status, headers, cause):
    mock_scan_http(monkeypatch, httpx.Response(status, headers=headers))
    found, unverified = await run_osint_scan('nessuno@example.com')
    assert found == []
    assert [(u['domain'], u['cause']) for u in unverified] == [('github.com', cause)]


@pytest.mark.anyio
async def test_github_empty_result_is_not_unverified(monkeypatch):
    mock_scan_http(monkeypatch, httpx.Response(200, json={'total_count': 0, 'items': [], 'incomplete_results': False}))
    assert await run_osint_scan('nessuno@example.com') == ([], [])


@pytest.mark.anyio
async def test_generic_exception_cause_is_observed_not_hint(monkeypatch):
    async def broken(email, client, out):
        raise RuntimeError('private email and token must not be exposed')

    async def negative(client, email):
        return None

    monkeypatch.setattr(osint, 'HOLEHE_MODULES', ['social_media.discord'])
    monkeypatch.setattr(osint.importlib, 'import_module', lambda name: SimpleNamespace(discord=broken))
    for name in ('check_gravatar', 'check_duolingo', 'check_github', 'check_spotify'):
        monkeypatch.setattr(osint, name, negative)
    found, unverified = await run_osint_scan('nessuno@example.com')
    assert found == []
    assert unverified == [{'domain': 'discord.com', 'cause': 'RuntimeError', 'reason': 'RuntimeError', 'hint': osint.KNOWN_UNRELIABLE['discord.com']}]
    assert 'private' not in str(unverified)


@pytest.mark.anyio
@pytest.mark.parametrize('failure', ['import', 'missing_function', 'execution', 'no_output'])
async def test_fallback_domain_mapping(monkeypatch, failure):
    async def module(email, client, out):
        if failure == 'execution':
            raise ValueError('private')

    def import_module(name):
        if failure == 'import':
            raise ImportError('private')
        if failure == 'missing_function':
            return SimpleNamespace()
        return SimpleNamespace(**{name.split('.')[-1]: module})

    monkeypatch.setattr(osint, 'HOLEHE_MODULES', ['mails.protonmail', 'music.lastfm', 'software.docker'])
    monkeypatch.setattr(osint.importlib, 'import_module', import_module)
    rows = await osint._run_holehe('nessuno@example.com', None)
    assert {row['domain'] for row in rows} == {'proton.me', 'last.fm', 'docker.com'}
    assert all(row.get('cause') for row in rows)


@pytest.mark.anyio
@pytest.mark.parametrize('probe,domain,negative,positive', NATIVE_CASES)
@pytest.mark.parametrize('case', ['negative', 'positive', 'http403', 'http429', 'timeout', 'exception', 'invalid_json', 'missing_fields'])
async def test_native_probe_three_outcomes(probe, domain, negative, positive, case):
    def handle(request):
        if case == 'timeout':
            raise httpx.ReadTimeout('private request details')
        if case == 'exception':
            raise RuntimeError('private request details')
        if case.startswith('http'):
            return httpx.Response(int(case[4:]))
        if case == 'invalid_json':
            return httpx.Response(200, text='<html>not JSON</html>')
        return httpx.Response(200, json=positive if case == 'positive' else negative if case == 'negative' else {})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
        result = await probe(client, 'nessuno@example.com')
    if case == 'positive':
        assert isinstance(result, ServiceEntry) and result.domain == domain
    elif case == 'negative':
        assert result is None
    else:
        assert result['domain'] == domain
        assert result['cause']
        assert 'private' not in str(result)
        if case.startswith('http'):
            assert result['cause'].startswith('HTTP ' + case[4:])


@pytest.mark.anyio
@pytest.mark.parametrize('payload', [
    {'total_count': 0, 'items': [], 'incomplete_results': True},
    {'total_count': 1, 'items': []},
    {'total_count': 0, 'items': 'invalid'},
])
async def test_github_invalid_or_incomplete_is_unverified(payload):
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda r: httpx.Response(200, json=payload))) as client:
        result = await osint.check_github(client, 'nessuno@example.com')
    assert result['domain'] == 'github.com' and result['cause']


@pytest.mark.anyio
async def test_slow_probes_preserve_completed_results(monkeypatch):
    async def get(self, url, **kwargs):
        if 'api.github.com' in url:
            return httpx.Response(200, json={'total_count': 1, 'items': [{'login': 'test'}]})
        await asyncio.Event().wait()

    async def slow_module(email, client, out):
        await asyncio.Event().wait()

    monkeypatch.setattr(osint, 'PROBE_TIMEOUT', 0.02)
    monkeypatch.setattr(httpx.AsyncClient, 'get', get)
    monkeypatch.setattr(osint, 'HOLEHE_MODULES', ['social_media.discord'])
    monkeypatch.setattr(osint.importlib, 'import_module', lambda name: SimpleNamespace(discord=slow_module))
    found, unverified = await run_osint_scan('nessuno@example.com')
    assert [s.domain for s in found] == ['github.com']
    assert {u['domain'] for u in unverified} == {'gravatar.com', 'duolingo.com', 'spotify.com', 'discord.com'}
    assert all(u['cause'] == 'TimeoutError' for u in unverified)
