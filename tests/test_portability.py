"""Exercise a relocated source tree and launcher without a GUI or credentials."""

import json
import os
from pathlib import Path
import shutil
import shlex
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def relocated(tmp_path):
    root = tmp_path / "CleanSlate con spazi"
    shutil.copytree(ROOT / "CleanSlate.app", root / "CleanSlate.app")
    shutil.copytree(ROOT / "cleanslate", root / "cleanslate", ignore=shutil.ignore_patterns("__pycache__"))
    return root


def fake_python(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    code = "import json, os, sys; print(json.dumps({'cwd': os.getcwd(), 'args': sys.argv[1:]}))"
    path.write_text(
        "#!/bin/sh\n"
        f'exec {shlex.quote(sys.executable)} -c {shlex.quote(code)} "$@"\n',
        encoding="utf-8",
    )
    path.chmod(0o755)


@pytest.mark.skipif(sys.platform == "win32", reason="macOS shell launcher")
@pytest.mark.parametrize("custom", [False, True])
def test_launcher_from_relocated_tree(relocated, tmp_path, custom):
    interpreter = tmp_path / "alt python" if custom else relocated / "venv/bin/python3"
    fake_python(interpreter)
    env = os.environ.copy()
    env.pop("CLEANSLATE_PYTHON", None)
    if custom:
        env["CLEANSLATE_PYTHON"] = str(interpreter)
    result = subprocess.run(
        ["/bin/bash", str(relocated / "CleanSlate.app/Contents/MacOS/CleanSlate")],
        cwd=tmp_path, env=env, capture_output=True, text=True, check=True,
    )
    assert json.loads(result.stdout) == {"cwd": str(relocated), "args": ["-m", "cleanslate.desktop"]}


@pytest.mark.skipif(sys.platform == "win32", reason="macOS shell launcher")
@pytest.mark.parametrize("override", [None, "relative/python", "/nonexistent/cleanslate/python"])
def test_launcher_missing_interpreter_explains_installation(relocated, tmp_path, override):
    env = os.environ.copy()
    env.pop("CLEANSLATE_PYTHON", None)
    if override is not None:
        env["CLEANSLATE_PYTHON"] = override
    result = subprocess.run(
        ["/bin/bash", str(relocated / "CleanSlate.app/Contents/MacOS/CleanSlate")],
        cwd=tmp_path, env=env, capture_output=True, text=True,
    )
    assert result.returncode == 1
    assert "REQUISITI.md" in result.stderr
    assert "CLEANSLATE_PYTHON" in result.stderr


def test_relocated_backend_serves_static_and_demo(relocated, tmp_path):
    code = '''
import os, sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from fastapi.testclient import TestClient
import cleanslate.web.app as module
assert Path(module.__file__).is_relative_to(Path(sys.argv[1]))
with TestClient(module.app) as client:
    for url in ("/", "/static/app.js", "/static/style.css", "/api/demo-data"):
        response = client.get(url)
        assert response.status_code == 200, (url, response.status_code)
    assert "services" in client.get("/api/demo-data").json()
    assert 'src="/static/app.js"' in client.get("/").text
'''
    subprocess.run(
        [sys.executable, "-I", "-c", code, str(relocated)],
        cwd=tmp_path, check=True, capture_output=True, text=True,
    )
