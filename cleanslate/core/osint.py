"""Asynchronous OSINT engine for discovering registered accounts from an email."""


import asyncio
import hashlib
import importlib
from functools import wraps
from typing import Any, Dict, List, Tuple, Union
import httpx

from cleanslate.core.models import DeletionDifficulty, ServiceCategory, ServiceEntry
from cleanslate.core.directory import lookup_service, normalize_domain

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
}

HOLEHE_MODULES = [
    "social_media.twitter",
    "social_media.pinterest",
    "social_media.discord",
    "social_media.patreon",
    "social_media.snapchat",
    "social_media.strava",
    "social_media.tumblr",
    "music.spotify",
    "music.soundcloud",
    "music.lastfm",
    "shopping.deliveroo",
    "software.docker",
    "mails.protonmail",
]

KNOWN_UNRELIABLE: Dict[str, str] = {
    "discord.com": "Il flusso di registrazione può richiedere un captcha.",
    "pinterest.com": "La risposta dell'endpoint può non avere la struttura attesa dal modulo.",
    "deliveroo.com": "L'endpoint può limitare o rifiutare le richieste automatiche.",
    "patreon.com": "Il modulo può fallire sia per errori di rete sia per risposte inattese.",
    "soundcloud.com": "L'estrazione del client ID dipende dalla struttura della pagina.",
    "tumblr.com": "L'estrazione dei token dipende dalla struttura della pagina.",
    "snapchat.com": "L'estrazione dei token dipende dal flusso di accesso.",
    "strava.com": "L'estrazione del token CSRF dipende dalla pagina di registrazione.",
}

HOLEHE_DOMAINS = {
    "twitter": "twitter.com", "pinterest": "pinterest.com", "discord": "discord.com",
    "patreon": "patreon.com", "snapchat": "snapchat.com", "strava": "strava.com",
    "tumblr": "tumblr.com", "spotify": "spotify.com", "soundcloud": "soundcloud.com",
    "lastfm": "last.fm", "deliveroo": "deliveroo.com", "docker": "docker.com",
    "protonmail": "proton.me",
}
PROBE_TIMEOUT = 20.0
NativeResult = Union[ServiceEntry, Dict[str, str], None]


def _unverified(domain: str, cause: str) -> Dict[str, str]:
    # reason remains an alias for older API clients, never an inferred explanation.
    result = {"domain": domain, "cause": cause, "reason": cause}
    if domain in KNOWN_UNRELIABLE:
        result["hint"] = KNOWN_UNRELIABLE[domain]
    return result


class _ProbeFailure(Exception):
    """A diagnostic assembled locally, without request data or server bodies."""


def _native_probe(domain):
    def decorate(fn):
        @wraps(fn)
        async def run(client, email) -> NativeResult:
            try:
                return await asyncio.wait_for(fn(client, email), timeout=PROBE_TIMEOUT)
            except _ProbeFailure as exc:
                return _unverified(domain, str(exc))
            except Exception as exc:
                return _unverified(domain, type(exc).__name__)
        return run
    return decorate


def _native_json(response):
    if response.status_code != 200:
        cause = f"HTTP {response.status_code}"
        if response.status_code == 429 or (response.status_code == 403 and response.headers.get("x-ratelimit-remaining") == "0"):
            cause += " (limite di richieste)"
        raise _ProbeFailure(cause)
    data = response.json()
    if not isinstance(data, dict):
        raise _ProbeFailure("Risposta JSON inattesa")
    return data


def _items(data, key):
    items = data.get(key)
    if not isinstance(items, list) or any(not isinstance(item, dict) for item in items):
        raise _ProbeFailure("Risposta JSON inattesa")
    return items


# 16 services verified across native probes + Holehe
OSINT_SERVICE_NAMES = [
    "Gravatar",
    "Duolingo",
    "GitHub",
    "Spotify",
    "Twitter/X",
    "Pinterest",
    "Discord",
    "Deliveroo",
    "Patreon",
    "SoundCloud",
    "Last.fm",
    "Snapchat",
    "Strava",
    "Docker Hub",
    "Tumblr",
    "Proton Mail",
]


@_native_probe("gravatar.com")
async def check_gravatar(client: httpx.AsyncClient, email: str) -> NativeResult:
    """Check if the email has a registered Gravatar / WordPress account."""
    email_clean = email.strip().lower()
    email_hash = hashlib.md5(email_clean.encode("utf-8")).hexdigest()
    url = f"https://en.gravatar.com/{email_hash}.json"
    
    resp = await client.get(url, timeout=4.0)
    data = _native_json(resp)
    entries = _items(data, "entry")
    if not entries:
        return None
    entry = entries[0]
    display_name = entry.get("displayName") or entry.get("preferredUsername") or "Utente Gravatar"
    return ServiceEntry(
        name="Gravatar / WordPress",
        domain="gravatar.com",
        category=ServiceCategory.ACCOUNT,
        found_via="osint",
        difficulty=DeletionDifficulty.EASY,
        delete_url="https://en.gravatar.com/support/deleting-your-account/",
        dpo_email="privacy@automattic.com",
        notes="Account collegato all'ecosistema WordPress.com e Automattic.",
        details={"username": display_name, "profile_url": entry.get("profileUrl")},
    )


@_native_probe("duolingo.com")
async def check_duolingo(client: httpx.AsyncClient, email: str) -> NativeResult:
    """Check if email is registered on Duolingo."""
    url = "https://www.duolingo.com/2017-06-30/users"
    resp = await client.get(url, params={"email": email.strip().lower()}, headers=DEFAULT_HEADERS, timeout=4.0)
    data = _native_json(resp)
    users = _items(data, "users")
    if users:
        user = users[0]
        dir_info = lookup_service("duolingo.com") or {}
        return ServiceEntry(
            name="Duolingo",
            domain="duolingo.com",
            category=ServiceCategory.ACCOUNT,
            found_via="osint",
            difficulty=dir_info.get("difficulty", DeletionDifficulty.EASY),
            delete_url=dir_info.get("delete_url", "https://drive-thru.duolingo.com/"),
            dpo_email=dir_info.get("dpo_email", "privacy@duolingo.com"),
            notes=dir_info.get("notes"),
            details={
                "username": user.get("username"),
                "streak": user.get("streak"),
            },
        )
    return None


@_native_probe("github.com")
async def check_github(client: httpx.AsyncClient, email: str) -> NativeResult:
    """Check if email is publicly linked to a GitHub account."""
    url = "https://api.github.com/search/users"
    headers = {**DEFAULT_HEADERS, "Accept": "application/vnd.github.v3+json"}
    resp = await client.get(url, params={"q": f"{email.strip().lower()} in:email"}, headers=headers, timeout=4.0)
    data = _native_json(resp)
    users = _items(data, "items")
    count = data.get("total_count")
    if type(count) is not int or count < 0 or bool(count) != bool(users):
        raise _ProbeFailure("Risposta JSON inattesa")
    if data.get("incomplete_results") is True:
        raise _ProbeFailure("Ricerca incompleta (incomplete_results=true)")
    if users:
        user = users[0]
        dir_info = lookup_service("github.com") or {}
        return ServiceEntry(
            name="GitHub",
            domain="github.com",
            category=ServiceCategory.ACCOUNT,
            found_via="osint",
            difficulty=dir_info.get("difficulty", DeletionDifficulty.EASY),
            delete_url=dir_info.get("delete_url"),
            dpo_email=dir_info.get("dpo_email"),
            notes=dir_info.get("notes"),
            details={
                "username": user.get("login"),
                "profile_url": user.get("html_url"),
            },
        )
    return None


@_native_probe("spotify.com")
async def check_spotify(client: httpx.AsyncClient, email: str) -> NativeResult:
    """Check Spotify registration via public signup validator endpoint."""
    url = "https://spclient.wg.spotify.com/signup/public/v1/account"
    resp = await client.get(url, params={"validate": "1", "email": email.strip().lower()}, headers=DEFAULT_HEADERS, timeout=4.0)
    data = _native_json(resp)
    status = data.get("status")
    if type(status) is not int or status not in (1, 20):
        raise _ProbeFailure("Risposta JSON inattesa (status Spotify)")
    if status == 20:
        dir_info = lookup_service("spotify.com") or {}
        return ServiceEntry(
            name="Spotify",
            domain="spotify.com",
            category=ServiceCategory.ACCOUNT,
            found_via="osint",
            difficulty=dir_info.get("difficulty", DeletionDifficulty.EASY),
            delete_url=dir_info.get("delete_url"),
            dpo_email=dir_info.get("dpo_email"),
            notes=dir_info.get("notes"),
        )
    return None


async def _run_holehe(email: str, client: httpx.AsyncClient) -> List[Dict[str, Any]]:
    """Run each module with its own result buffer and time limit."""
    async def worker(mod_path):
        short = mod_path.split(".")[-1]
        domain = HOLEHE_DOMAINS[short]
        out = []
        try:
            full_name = mod_path if mod_path.startswith("holehe.modules.") else f"holehe.modules.{mod_path}"
            mod = importlib.import_module(full_name)
            fn = getattr(mod, short)
            await asyncio.wait_for(fn(email, client, out), timeout=PROBE_TIMEOUT)
        except Exception as exc:
            out.append({"domain": domain, "cause": type(exc).__name__})
        if not out:
            out.append({"domain": domain, "cause": "Nessun esito restituito dal modulo"})
        for item in out:
            item.setdefault("domain", domain)
        return out

    batches = await asyncio.gather(*(worker(path) for path in HOLEHE_MODULES))
    return [item for batch in batches for item in batch]


async def run_osint_scan(email: str) -> Tuple[List[ServiceEntry], List[Dict[str, str]]]:
    """Return found services and unverified domain/cause details (optional hint)."""
    results: List[ServiceEntry] = []
    unverified: List[Dict[str, str]] = []
    seen_domains = set()
    unverified_domains = set()

    async with httpx.AsyncClient(timeout=6.0, follow_redirects=True) as client:
        probes = [
            ("gravatar.com", check_gravatar), ("duolingo.com", check_duolingo),
            ("github.com", check_github), ("spotify.com", check_spotify),
        ]
        probe_results, holehe_raw = await asyncio.gather(
            asyncio.gather(*(fn(client, email) for _, fn in probes), return_exceptions=True),
            _run_holehe(email, client),
        )

    for (domain, _), res in zip(probes, probe_results):
        if isinstance(res, ServiceEntry) and res.domain not in seen_domains:
            results.append(res)
            seen_domains.add(res.domain)
        elif isinstance(res, dict) or isinstance(res, Exception):
            detail = res if isinstance(res, dict) else _unverified(domain, type(res).__name__)
            unverified.append(detail)
            unverified_domains.add(domain)

    for item in holehe_raw:
        if not isinstance(item, dict):
            continue

        raw_domain = item.get("domain") or HOLEHE_DOMAINS.get(item.get("name"))
        domain = normalize_domain(raw_domain) if raw_domain else ""
        if not domain:
            continue

        cause = item.get("cause")
        if not cause and item.get("rateLimit") is True:
            cause = "rateLimit=True restituito dal modulo Holehe"
        if not cause and item.get("exists") is not True and item.get("exists") is not False:
            cause = "Esito inatteso dal modulo Holehe"
        if cause:
            if domain not in unverified_domains:
                unverified.append(_unverified(domain, cause))
                unverified_domains.add(domain)
            continue

        if item.get("exists") is True:
            if domain in seen_domains:
                continue

            dir_info = lookup_service(domain) or (lookup_service(item.get("name")) if item.get("name") else {}) or {}
            name = dir_info.get("name") or (item.get("name").capitalize() if item.get("name") else domain)
            difficulty = dir_info.get("difficulty", DeletionDifficulty.UNKNOWN)
            delete_url = dir_info.get("delete_url")
            dpo_email = dir_info.get("dpo_email")
            notes = dir_info.get("notes") or "Account attivo confermato da probe API endpoint."

            entry = ServiceEntry(
                name=name,
                domain=domain,
                category=ServiceCategory.ACCOUNT,
                found_via="osint",
                difficulty=difficulty,
                delete_url=delete_url,
                dpo_email=dpo_email,
                notes=notes,
                details={
                    "phone_linked": bool(item.get("phoneNumber")),
                    "recovery_email": item.get("emailrecovery"),
                },
            )
            results.append(entry)
            seen_domains.add(domain)

    # Filter verified domains out of unverified
    unverified = [u for u in unverified if u["domain"] not in seen_domains]

    return results, unverified
