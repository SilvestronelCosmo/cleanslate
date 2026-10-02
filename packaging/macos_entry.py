"""Desktop entry point and offline diagnostics for the frozen application."""

import asyncio
import importlib
import json
from pathlib import Path
import sys


def self_test():
    import httpx
    import ssl
    import certifi
    from cleanslate.desktop import configure_macos_name
    from cleanslate.core.osint import HOLEHE_MODULES
    from cleanslate.web.app import app
    from Foundation import NSBundle, NSProcessInfo
    import webview.platforms.cocoa
    from keyring.backends import macOS

    assert getattr(sys, "frozen", False), "Eseguire il binario del pacchetto"
    configure_macos_name()
    assert NSProcessInfo.processInfo().processName() == "CleanSlate"
    assert NSBundle.mainBundle().infoDictionary()["CFBundleName"] == "CleanSlate"
    for name in HOLEHE_MODULES:
        importlib.import_module("holehe.modules." + name)
    context = ssl.create_default_context(cafile=certifi.where())
    assert context.verify_mode == ssl.CERT_REQUIRED and context.check_hostname
    assert context.cert_store_stats()["x509_ca"] > 0
    assert macOS.Keyring

    async def check_api():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            for url in ("/", "/static/app.js", "/static/style.css"):
                response = await client.get(url)
                assert response.status_code == 200 and response.content, url
            response = await client.get("/api/demo-data")
            assert response.status_code == 200
            data = response.json()
            assert data["total_services"] > 0
            return data["total_services"]

    count = asyncio.run(check_api())
    return {"ok": True, "frozen": True, "demo_services": count,
            "holehe_modules": len(HOLEHE_MODULES), "python": sys.version.split()[0]}


def gui_test(report):
    import time
    import webview
    from cleanslate import desktop

    original_start = webview.start
    result = {"ok": False, "error": "GUI non completata"}

    def probe():
        try:
            window = webview.windows[0]
            assert window.events.loaded.wait(20), "Timeout caricamento pagina"
            window.evaluate_js("document.getElementById('btn-load-demo').click()")
            for _ in range(100):
                count = window.evaluate_js("currentScanData.isDemo ? currentScanData.services.length : 0")
                if count:
                    result.update(ok=True, demo_services=count)
                    result.pop("error", None)
                    break
                time.sleep(0.1)
            assert result["ok"], "Demo non caricata nella GUI"
        except Exception as exc:
            result.update(ok=False, error=type(exc).__name__ + ": " + str(exc))
        finally:
            report.write_text(json.dumps(result), encoding="utf-8")
            webview.windows[0].destroy()

    def start(**kwargs):
        # The checker supplies an isolated HOME; private mode also avoids old web data.
        kwargs["private_mode"] = True
        return original_start(probe, **kwargs)

    webview.start = start
    desktop.main()


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--self-test":
        Path(sys.argv[2]).write_text(json.dumps(self_test()), encoding="utf-8")
    elif len(sys.argv) == 3 and sys.argv[1] == "--gui-self-test":
        gui_test(Path(sys.argv[2]))
    else:
        from cleanslate.desktop import main
        main()
