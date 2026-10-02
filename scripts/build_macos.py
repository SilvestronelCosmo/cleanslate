"""Build a local review ZIP; no publication, accounts or user data are involved."""

import hashlib
from importlib.metadata import distributions
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tarfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
NAME = "CleanSlate-1.0.0-macos-arm64"
SOURCE_FILES = ("README.md", "REQUISITI.md", "LICENSE", "THIRD_PARTY_NOTICES.md", "RELEASE_NOTES.md", "requirements.txt")
SOURCE_DIRS = {"cleanslate": {".py", ".js", ".css", ".html"}, "tests": {".py", ".cjs"},
               "scripts": {".py"}, "packaging": {".py", ".spec", ".txt"}, "docs": {".md"},
               "CleanSlate.app": {".plist", ".icns"}}


def run(*args, **kwargs):
    return subprocess.run(args, check=True, cwd=ROOT, **kwargs)


def source_files():
    paths = [ROOT / name for name in SOURCE_FILES]
    paths.append(ROOT / "CleanSlate.app/Contents/MacOS/CleanSlate")
    for directory, suffixes in SOURCE_DIRS.items():
        paths.extend(path for path in (ROOT / directory).rglob("*")
                     if path.is_file() and not path.is_symlink() and path.suffix in suffixes
                     and not any(part.startswith(".") or part == "__pycache__" for part in path.relative_to(ROOT).parts))
    return sorted(set(paths))


def dependency_sources(legal):
    cache = ROOT / "build/dependency-sources"
    cache.mkdir(parents=True, exist_ok=True)
    inventory = []
    missing = []
    for dist in sorted(distributions(), key=lambda d: d.metadata["Name"].lower()):
        name, version = dist.metadata["Name"], dist.version
        print(f"Sorgenti e licenze: {name} {version}", flush=True)
        metadata_path = cache / f"{name}-{version}.json"
        if not metadata_path.exists():
            with urllib.request.urlopen(f"https://pypi.org/pypi/{name}/{version}/json", timeout=30) as response:
                metadata_path.write_bytes(response.read())
        metadata = json.loads(metadata_path.read_text())
        sdist = next(item for item in metadata["urls"] if item["packagetype"] == "sdist")
        archive = cache / sdist["filename"]
        if not archive.exists():
            with urllib.request.urlopen(sdist["url"], timeout=60) as response:
                archive.write_bytes(response.read())
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        if digest != sdist["digests"]["sha256"]:
            raise RuntimeError(f"SHA-256 non valido: {archive.name}")
        target = legal / "python-packages" / f"{name}-{version}"
        target.mkdir(parents=True)
        license_files = []
        # Read license members only; never extract paths or links from an upstream archive.
        with tarfile.open(archive) as source:
            for member in source.getmembers():
                basename = Path(member.name).name
                if member.isfile() and basename.lower().startswith(("license", "licence", "copying", "notice", "copyright")):
                    output = target / f"{len(license_files):03d}-{basename}"
                    output.write_bytes(source.extractfile(member).read())
                    license_files.append(output.name)
        if not license_files and name == "bs4":
            (target / "METADATA.txt").write_text(dist.read_text("METADATA"), encoding="utf-8")
            license_files = ["METADATA.txt"]
        if not license_files and (name, version) == ("holehe", "1.61"):
            shutil.copy2(ROOT / "LICENSE", target / "GPL-3.0.txt")
            (target / "METADATA.txt").write_text(dist.read_text("METADATA"), encoding="utf-8")
            (target / "PROVENIENZA.txt").write_text("Holehe 1.61, autore megadose. GPLv3 dichiarata nei metadati dello sdist.\nTesto GPLv3 completo aggiunto perché omesso dallo sdist.\nFonte upstream: https://github.com/megadose/holehe/blob/master/LICENSE.md\n")
            license_files = ["GPL-3.0.txt", "METADATA.txt", "PROVENIENZA.txt"]
        if not license_files and (name, version) == ("proxy_tools", "0.1.0"):
            shutil.copy2(ROOT / "packaging/licenses/proxy_tools-0.1.0.txt", target / "LICENSE.txt")
            shutil.copy2(ROOT / "packaging/licenses/PROVENIENZA.txt", target / "PROVENIENZA.txt")
            license_files = ["LICENSE.txt", "PROVENIENZA.txt"]
        if not license_files:
            missing.append(name)
        inventory.append({"name": name, "version": version, "license": metadata["info"].get("license_expression") or metadata["info"].get("license"),
                          "source": archive.name, "url": sdist["url"], "sha256": digest, "license_files": license_files})
    (legal / "python-environment.json").write_text(json.dumps(inventory, indent=2), encoding="utf-8")
    if missing:
        raise RuntimeError(f"Testo di licenza mancante nello sdist di: {', '.join(missing)}")
    return inventory


def native_licenses(legal, analysis):
    packages = {}
    for item in analysis["binaries"]:
        source = Path(item["source"]).resolve()
        if source.is_relative_to(Path(sys.prefix).resolve()):
            continue  # Covered by the Python distributions' source archives and notices.
        parts = source.parts
        if "Cellar" not in parts:
            raise RuntimeError(f"Provenienza nativa da inventariare: {source.name}")
        index = parts.index("Cellar")
        package = Path(*parts[:index + 3])
        packages[str(package)] = package
    native_inventory = []
    for package in packages.values():
        target = legal / "native" / package.parent.name / package.name
        target.mkdir(parents=True)
        files = [p for p in package.rglob("*") if p.is_file() and not p.is_symlink()
                 and len(p.relative_to(package).parts) <= 4
                 and p.name.lower().startswith(("license", "licence", "copying", "notice", "copyright"))]
        if not files:
            raise RuntimeError(f"Licenza nativa mancante: {package.parent.name}")
        for i, path in enumerate(files):
            shutil.copy2(path, target / f"{i:03d}-{path.name}")
        native_inventory.append({"name": package.parent.name, "version": package.name, "license_files": len(files)})
    (legal / "native-libraries.json").write_text(json.dumps(native_inventory, indent=2))


def main():
    if sys.platform != "darwin" or platform.machine() != "arm64":
        raise SystemExit("Questa ricetta richiede macOS su Apple Silicon.")
    if Path(sys.prefix).resolve() == Path(sys.base_prefix).resolve():
        raise SystemExit("Usare un venv dedicato alla build.")
    run(sys.executable, "-m", "pip", "--isolated", "check")
    legal = ROOT / "build/legal"
    if legal.exists():
        shutil.rmtree(legal)
    legal.mkdir(parents=True)
    inventory = dependency_sources(legal)
    for name in ("LICENSE", "THIRD_PARTY_NOTICES.md"):
        shutil.copy2(ROOT / name, legal / name)
    env = os.environ.copy()
    env["PYINSTALLER_CONFIG_DIR"] = str(ROOT / "build/pyinstaller-cache")
    run(sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--distpath", "build/frozen",
        "--workpath", "build/pyinstaller", "packaging/cleanslate.spec", env=env)
    analysis = json.loads((ROOT / "build/analysis.json").read_text())
    native_licenses(legal, analysis)
    app = ROOT / "build/frozen/CleanSlate.app"
    shutil.copytree(legal, app / "Contents/Resources/legal", dirs_exist_ok=True)
    run("/usr/bin/codesign", "--force", "--sign", "-", str(app))
    run("/usr/bin/codesign", "--verify", "--deep", "--strict", str(app))

    stage = ROOT / "build/package" / NAME
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True)
    shutil.copytree(app, stage / "CleanSlate.app", symlinks=True)
    shutil.copy2(ROOT / "docs/INSTALLAZIONE_MACOS.md", stage / "LEGGIMI.md")
    shutil.copy2(ROOT / "LICENSE", stage / "LICENSE")
    for path in source_files():
        target = stage / "sorgenti" / path.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
    deps = stage / "sorgenti-dipendenze"
    deps.mkdir()
    for item in inventory:
        shutil.copy2(ROOT / "build/dependency-sources" / item["source"], deps / item["source"])
    (stage / "sorgenti/packaging/requirements-resolved.txt").write_text("\n".join(f"{i['name']}=={i['version']}" for i in inventory) + "\n")
    manifest = {"version": "1.0.0", "architecture": "arm64", "tested_macos": platform.mac_ver()[0],
                "python": platform.python_version(), "signing": "ad-hoc; non notarizzata", "review_required": True,
                "python_modules": analysis["modules"], "native_binaries": [item["name"] for item in analysis["binaries"]],
                "source_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in source_files()}}
    (stage / "BUILD-INFO.json").write_text(json.dumps(manifest, indent=2))
    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)
    archive = dist / f"{NAME}.zip"
    if archive.exists():
        archive.unlink()
    run("/usr/bin/ditto", "-c", "-k", "--keepParent", "--norsrc", str(stage), str(archive))
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    (dist / f"{NAME}.sha256").write_text(f"{digest}  {archive.name}\n")
    print(f"Creato {archive.name}: {archive.stat().st_size / 1024**2:.1f} MiB, SHA-256 {digest}")


if __name__ == "__main__":
    main()
