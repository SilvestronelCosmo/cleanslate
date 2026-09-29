"""Asynchronous OSINT engine for discovering registered accounts from an email."""


import asyncio
import hashlib
import importlib
from typing import Any, Dict, List, Optional, Tuple
import httpx

from cleanslate.core.models import DeletionDifficulty, ServiceCategory, ServiceEntry
from cleanslate.core.directory import lookup_service, normalize_domain

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
}

# Exactly 14 active Holehe modules
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
    "programing.github",
    "shopping.deliveroo",
    "software.docker",
    "mails.protonmail",
]

# Exactly 16 services verified across native probes + Holehe
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


async def check_gravatar(client: httpx.AsyncClient, email: str) -> Optional[ServiceEntry]:
    """Check if the email has a registered Gravatar / WordPress account."""
    email_clean = email.strip().lower()
    email_hash = hashlib.md5(email_clean.encode("utf-8")).hexdigest()
    url = f"https://en.gravatar.com/{email_hash}.json"
    
    try:
        resp = await client.get(url, timeout=4.0)
        if resp.status_code == 200:
            data = resp.json()
            entry = data.get("entry", [{}])[0]
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
    except Exception:
        pass
    return None


async def check_duolingo(client: httpx.AsyncClient, email: str) -> Optional[ServiceEntry]:
    """Check if email is registered on Duolingo."""
    url = "https://www.duolingo.com/2017-06-30/users"
    try:
        resp = await client.get(url, params={"email": email.strip().lower()}, headers=DEFAULT_HEADERS, timeout=4.0)
        if resp.status_code == 200:
            data = resp.json()
            users = data.get("users", [])
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
    except Exception:
        pass
    return None


async def check_github(client: httpx.AsyncClient, email: str) -> Optional[ServiceEntry]:
    """Check if email is publicly linked to a GitHub account."""
    url = "https://api.github.com/search/users"
    headers = {**DEFAULT_HEADERS, "Accept": "application/vnd.github.v3+json"}
    try:
        resp = await client.get(url, params={"q": f"{email.strip().lower()} in:email"}, headers=headers, timeout=4.0)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("total_count", 0) > 0:
                user = data.get("items", [])[0]
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
    except Exception:
        pass
    return None


async def check_spotify(client: httpx.AsyncClient, email: str) -> Optional[ServiceEntry]:
    """Check Spotify registration via public signup validator endpoint."""
    url = "https://spclient.wg.spotify.com/signup/public/v1/account"
    try:
        resp = await client.get(url, params={"validate": "1", "email": email.strip().lower()}, headers=DEFAULT_HEADERS, timeout=4.0)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("status") == 20 or "email_exists" in str(data):
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
    except Exception:
        pass
    return None


async def _run_holehe(email: str, client: httpx.AsyncClient) -> List[Dict[str, Any]]:
    """Run selected Holehe modules asynchronously and gather raw results."""
    out: List[Dict[str, Any]] = []
    tasks = []

    for mod_path in HOLEHE_MODULES:
        short = mod_path.split(".")[-1]
        try:
            full_name = mod_path if mod_path.startswith("holehe.modules.") else f"holehe.modules.{mod_path}"
            mod = importlib.import_module(full_name)
            func = getattr(mod, short, None)
            if func:
                async def _worker(fn=func, s=short):
                    try:
                        await fn(email, client, out)
                    except Exception:
                        out.append({"name": s, "domain": f"{s}.com", "rateLimit": True, "exists": False})
                tasks.append(_worker())
            else:
                out.append({"name": short, "domain": f"{short}.com", "rateLimit": True, "exists": False})
        except Exception:
            out.append({"name": short, "domain": f"{short}.com", "rateLimit": True, "exists": False})

    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)

    return out


async def run_osint_scan(email: str) -> Tuple[List[ServiceEntry], List[str]]:
    """Run native parallel probes + Holehe module suite against target email."""
    results: List[ServiceEntry] = []
    unverified: List[str] = []
    seen_domains = set()
    unverified_domains = set()

    async def _scan():
        async with httpx.AsyncClient(timeout=6.0, follow_redirects=True) as client:
            native_tasks = [
                check_gravatar(client, email),
                check_duolingo(client, email),
                check_github(client, email),
                check_spotify(client, email),
            ]
            probes_res, holehe_raw = await asyncio.gather(
                asyncio.gather(*native_tasks, return_exceptions=True),
                _run_holehe(email, client),
                return_exceptions=True,
            )
            return (
                probes_res if isinstance(probes_res, (list, tuple)) else [],
                holehe_raw if isinstance(holehe_raw, (list, tuple)) else [],
            )

    try:
        probe_results, holehe_raw = await asyncio.wait_for(_scan(), timeout=25.0)
    except asyncio.TimeoutError:
        probe_results, holehe_raw = [], []

    for res in probe_results:
        if isinstance(res, ServiceEntry) and res.domain not in seen_domains:
            results.append(res)
            seen_domains.add(res.domain)

    for item in holehe_raw:
        if not isinstance(item, dict):
            continue

        raw_domain = item.get("domain") or (f"{item['name']}.com" if item.get("name") else None)
        domain = normalize_domain(raw_domain) if raw_domain else ""
        if not domain:
            continue

        if item.get("rateLimit") is True:
            if domain not in unverified_domains:
                unverified.append(domain)
                unverified_domains.add(domain)

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
    unverified = [d for d in unverified if d not in seen_domains]

    return results, unverified
