"""Install and test a source-only copy in a fresh temporary virtual environment."""

from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile
import venv


def main():
    source = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    for name in ("PYTHONPATH", "PYTHONHOME", "PYTEST_ADDOPTS", "PYTEST_PLUGINS"):
        env.pop(name, None)
    env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    with tempfile.TemporaryDirectory(prefix="cleanslate-portability-") as temporary:
        root = Path(temporary) / "CleanSlate portable copy"
        root.mkdir()
        for name in ("cleanslate", "tests", "CleanSlate.app"):
            shutil.copytree(source / name, root / name, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
        shutil.copy2(source / "requirements.txt", root / "requirements.txt")
        venv.EnvBuilder(with_pip=True).create(root / "venv")
        python = root / "venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")

        def run(*args):
            subprocess.run([str(python), *args], cwd=root, env=env, check=True)

        run("-m", "pip", "--isolated", "install", "--disable-pip-version-check", "--no-cache-dir", "-r", "requirements.txt")
        run("-m", "pip", "--isolated", "check")
        run("-c", "import webview; import cleanslate.desktop; import cleanslate.web.app")
        if sys.platform == "darwin":
            run("-c", "from cleanslate.desktop import configure_macos_name; configure_macos_name(); from Foundation import NSProcessInfo, NSBundle; assert NSProcessInfo.processInfo().processName() == 'CleanSlate'; assert NSBundle.mainBundle().infoDictionary()['CFBundleName'] == 'CleanSlate'")
        run("-m", "pytest", "-p", "anyio.pytest_plugin", "-q")
        run("-m", "cleanslate.cli", "directory", "netflix")
        print("PASS: installazione pulita e copia spostata, senza scansioni reali.", flush=True)


if __name__ == "__main__":
    main()
