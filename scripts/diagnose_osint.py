"""Repeat the phase B network investigation with a fixed fictitious address."""

import asyncio
from datetime import datetime, timezone
import importlib
from importlib.metadata import version
import json

import httpx

MODULES = (
    "shopping.deliveroo", "music.soundcloud", "social_media.pinterest",
    "social_media.patreon", "social_media.discord", "social_media.tumblr",
    "social_media.snapchat", "social_media.strava",
)
EMAIL = "nessuno@example.com"


async def diagnose(module):
    observations = []
    output = []

    async def observe(response):
        await response.aread()
        signals = []
        body = response.text
        if '"captcha-required"' in body:
            signals.append("captcha-required")
        if module.endswith("snapchat") and 'data-xsrf="' not in body:
            signals.append("data-xsrf assente")
        if module.endswith("strava") and "/register/free" in response.request.url.path:
            signals.append("csrf-token presente" if '<meta name="csrf-token" content="' in body else "csrf-token assente")
        observations.append({
            "method": response.request.method,
            "endpoint": str(response.request.url.copy_with(query=None)),
            "http": response.status_code,
            "signals": signals,
        })

    exception = None
    async with httpx.AsyncClient(timeout=6.0, follow_redirects=True, event_hooks={"response": [observe]}) as client:
        try:
            if module == "github":
                response = await client.get("https://api.github.com/search/users", params={"q": f"{EMAIL} in:email"})
                if response.status_code == 200:
                    data = response.json()
                    output.append({"total_count": data.get("total_count"), "incomplete_results": data.get("incomplete_results")})
            else:
                imported = importlib.import_module("holehe.modules." + module)
                await asyncio.wait_for(getattr(imported, module.split(".")[-1])(EMAIL, client, output), timeout=20)
        except Exception as exc:
            exception = type(exc).__name__
    return {
        "module": module, "requests": observations, "exception": exception,
        "results": [{k: row[k] for k in ("domain", "exists", "rateLimit", "total_count", "incomplete_results") if k in row} for row in output],
    }


async def main():
    # Sequential modules make it easier to attribute each observation and avoid bursts.
    results = [await diagnose(module) for module in (*MODULES, "github")]
    print(json.dumps({"date_utc": datetime.now(timezone.utc).isoformat(), "holehe": version("holehe"), "email": EMAIL, "observations": results}, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
