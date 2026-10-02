"""Check the exact ZIP in a relocated, clean environment; optional real WebKit demo."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import plistlib
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
NAME = "CleanSlate-1.0.0-macos-arm64"


def run(*args, **kwargs):
    try:
        return subprocess.run(args, check=True, capture_output=True, text=True, **kwargs)
    except subprocess.CalledProcessError as exc:
        print(exc.stdout, exc.stderr, file=sys.stderr)
        raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gui", action="store_true", help="Apre WebKit, carica la demo e chiude la finestra")
    args = parser.parse_args()
    archive = ROOT / "dist" / f"{NAME}.zip"
    checksum = (ROOT / "dist" / f"{NAME}.sha256").read_text().split()[0]
    assert hashlib.sha256(archive.read_bytes()).hexdigest() == checksum, "Checksum ZIP"
    with zipfile.ZipFile(archive) as package:
        assert package.testzip() is None, "ZIP corrotto"
        for name in package.namelist():
            parts = Path(name).parts
            assert not name.startswith("/") and ".." not in parts, name
            assert not set(parts) & {".git", ".officina", "venv", ".cleanslate", "profiles.json"}, name
            assert not any(part == ".env" or part.startswith(".env.") for part in parts), name
    with tempfile.TemporaryDirectory(prefix="CleanSlate package con spazi ") as temporary:
        root = Path(temporary).resolve()
        run("/usr/bin/ditto", "-x", "-k", str(archive), str(root))
        folder = root / NAME
        app = folder / "CleanSlate.app"
        binary = app / "Contents/MacOS/CleanSlate"
        assert "arm64" in run("/usr/bin/file", str(binary)).stdout
        plist = plistlib.loads((app / "Contents/Info.plist").read_bytes())
        assert plist["CFBundleName"] == "CleanSlate"
        assert plist["CFBundleShortVersionString"] == "1.0.0"
        run("/usr/bin/codesign", "--verify", "--deep", "--strict", str(app))
        for path in app.rglob("*"):
            if path.is_symlink():
                assert path.resolve().is_relative_to(app), str(path)
        info = json.loads((folder / "BUILD-INFO.json").read_text())
        for relative, digest in info["source_sha256"].items():
            assert hashlib.sha256((folder / "sorgenti" / relative).read_bytes()).hexdigest() == digest
            assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == digest, f"ZIP da ricostruire: {relative} è cambiato"
        legal = app / "Contents/Resources/legal"
        for item in json.loads((legal / "python-environment.json").read_text()):
            source = folder / "sorgenti-dipendenze" / item["source"]
            assert hashlib.sha256(source.read_bytes()).hexdigest() == item["sha256"]
            for filename in item["license_files"]:
                assert (legal / "python-packages" / f"{item['name']}-{item['version']}" / filename).stat().st_size > 0
        assert json.loads((legal / "native-libraries.json").read_text())

        # Inspect every shipped Mach-O load command, including extension modules.
        native_count = 0
        for path in app.rglob("*"):
            if not path.is_file() or path.is_symlink():
                continue
            with path.open("rb") as stream:
                magic = stream.read(4)
            if magic not in (b"\xcf\xfa\xed\xfe", b"\xce\xfa\xed\xfe", b"\xca\xfe\xba\xbe", b"\xca\xfe\xba\xbf"):
                continue
            native_count += 1
            commands = run("/usr/bin/otool", "-l", str(path)).stdout
            assert not any(prefix in commands for prefix in ("/opt/homebrew", "/Users/", "/Library/Frameworks/Python")), path.name
            dependencies = run("/usr/bin/otool", "-L", str(path)).stdout.splitlines()[1:]
            for line in dependencies:
                dependency = line.strip().split(" (", 1)[0]
                assert dependency.startswith(("@", "/System/Library/", "/usr/lib/")), dependency

        home = root / "home"
        home.mkdir()
        env = {"HOME": str(home), "PATH": "/usr/bin:/bin:/usr/sbin:/sbin", "TMPDIR": str(root), "LANG": "en_US.UTF-8"}
        report = root / "self-test.json"
        run(str(binary), "--self-test", str(report), cwd=root, env=env, timeout=60)
        result = json.loads(report.read_text())
        assert result["ok"] and result["frozen"] and result["holehe_modules"] == 13, result
        assert not (home / ".cleanslate/profiles.json").exists()
        print(f"PASS: ZIP, checksum, firma ad-hoc, sorgenti, licenze, {native_count} Mach-O, runtime isolato: {result}")
        if args.gui:
            report = root / "gui-test.json"
            run(str(binary), "--gui-self-test", str(report), cwd=root, env=env, timeout=60)
            result = json.loads(report.read_text())
            assert result["ok"] and result["demo_services"] > 0, result
            assert not (home / ".cleanslate/profiles.json").exists()
            print(f"PASS: finestra Cocoa/WebKit e demo: {result}")


if __name__ == "__main__":
    main()
