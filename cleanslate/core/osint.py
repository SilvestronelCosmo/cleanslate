"""Asynchronous OSINT engine for discovering registered accounts from an email."""

import hashlib
import asyncio
from typing import List, Optional, Dict, Any
import httpx
import trio
import holehe.core

from cleanslate.core.models import ServiceEntry, ServiceCategory, DeletionDifficulty
from cleanslate.core.directory import lookup_service, normalize_domain

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
}

# High-confidence platforms from Holehe to audit in parallel
TARGET_HOLEHE_MODULES = [
    "twitter",
    "github",
    "spotify",
    "pinterest",
    "discord",
    "deliveroo",
    "patreon",
    "soundcloud",
    "lastfm",
    "snapchat",
    "strava",
    "docker",
    "vimeo",
    "tumblr",
    "protonmail",
    "chess",
    "duolingo",
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
    url = f"https://www.duolingo.com/2017-06-30/users?email={email.strip().lower()}"
    try:
        resp = await client.get(url, headers=DEFAULT_HEADERS, timeout=4.0)
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
    url = f"https://api.github.com/search/users?q={email.strip().lower()}+in:email"
    headers = {**DEFAULT_HEADERS, "Accept": "application/vnd.github.v3+json"}
    try:
        resp = await client.get(url, headers=headers, timeout=4.0)
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
    url = f"https://spclient.wg.spotify.com/signup/public/v1/account?validate=1&email={email.strip().lower()}"
    try:
        resp = await client.get(url, headers=DEFAULT_HEADERS, timeout=4.0)
        if resp.status_code == 200:
            data = resp.json()
            # status 20 indicates email is already taken / registered
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


def _run_holehe_sync(email: str) -> List[Dict[str, Any]]:
    """Trio worker running Holehe modules."""
    async def worker():
        out = []
        modules = holehe.core.import_submodules("holehe.modules")
        async with httpx.AsyncClient(timeout=4.0) as client:
            for mod_name, mod in modules.items():
                short = mod_name.split(".")[-1]
                if short in TARGET_HOLEHE_MODULES:
                    func = getattr(mod, short, None)
                    if func:
                        try:
                            await func(email, client, out)
                        except Exception:
                            pass
        return out

    try:
        return trio.run(worker)
    except Exception:
        return []


async def run_osint_scan(email: str) -> List[ServiceEntry]:
    """Run native parallel probes + Holehe module suite against target email."""
    results: List[ServiceEntry] = []
    seen_domains = set()

    # 1. Native high-speed async probes
    async with httpx.AsyncClient(timeout=5.0, follow_redirects=True) as client:
        native_probes = [
            check_gravatar(client, email),
            check_duolingo(client, email),
            check_github(client, email),
            check_spotify(client, email),
        ]
        probe_results = await asyncio.gather(*native_probes, return_exceptions=True)
        for res in probe_results:
            if isinstance(res, ServiceEntry) and res.domain not in seen_domains:
                results.append(res)
                seen_domains.add(res.domain)

    # 2. Run Holehe module suite in thread
    holehe_raw = await asyncio.to_thread(_run_holehe_sync, email)
    for item in holehe_raw:
        if item.get("exists") is True:
            domain = normalize_domain(item.get("domain") or item.get("name") + ".com")
            if domain in seen_domains:
                continue

            dir_info = lookup_service(domain) or lookup_service(item.get("name")) or {}
            name = dir_info.get("name") or item.get("name").capitalize()
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

    return results
