"""Profile storage tests; every Keychain operation is simulated."""

import json
import subprocess
from unittest.mock import Mock

import keyring
import pytest

from cleanslate.core import keychain


@pytest.fixture(autouse=True)
def simulated_keychain(tmp_path, monkeypatch):
    monkeypatch.setattr(keychain, "CONFIG_DIR", str(tmp_path))
    monkeypatch.setattr(keychain, "CONFIG_FILE", str(tmp_path / "profiles.json"))
    monkeypatch.setattr(subprocess, "run", Mock(side_effect=AssertionError("Subprocess forbidden")))
    backend = Mock()
    backend.get_password.return_value = None
    from keyring.backends import macOS
    monkeypatch.setattr(macOS, "Keyring", Mock(return_value=backend))
    monkeypatch.setattr(keychain, "platform", "darwin", raising=False)
    return backend


def test_save_and_load_profile(simulated_keychain):
    name = keychain.save_profile("IMAP.EXAMPLE.COM", 993, "User@example.com", "fake-secret")
    assert name == "user@example.com@imap.example.com:993"
    assert keychain.load_profiles() == [{
        "name": name, "host": "imap.example.com", "port": 993, "username": "User@example.com",
    }]
    assert keychain.load_profile(name) == keychain.load_profiles()[0]
    simulated_keychain.set_password.assert_called_once_with(keychain.SERVICE_NAME, name, "fake-secret")


def test_get_password_found(simulated_keychain):
    simulated_keychain.get_password.return_value = " fake-secret "
    assert keychain.get_password("profile") == " fake-secret "


def test_get_password_not_found(simulated_keychain):
    assert keychain.get_password("missing") is None


def test_delete_profile(simulated_keychain):
    name = keychain.save_profile("imap.example.com", 993, "user@example.com", "fake-secret")
    keychain.delete_profile(name)
    assert keychain.load_profiles() == []
    simulated_keychain.delete_password.assert_called_once_with(keychain.SERVICE_NAME, name)


def test_save_profile_no_password_in_file(simulated_keychain):
    keychain.save_profile("imap.example.com", 993, "user@example.com", "fake-secret")
    from pathlib import Path
    content = Path(keychain.CONFIG_FILE).read_text()
    assert "password" not in content
    assert "fake-secret" not in content


def test_load_profiles_empty():
    assert keychain.load_profiles() == []


def test_profiles_same_user_different_host_do_not_collide(simulated_keychain):
    first = keychain.save_profile("imap.first.example", 993, "user@example.com", "first-fake-secret")
    second = keychain.save_profile("imap.second.example", 993, "user@example.com", "second-fake-secret")
    third = keychain.save_profile("imap.first.example", 1993, "user@example.com", "third-fake-secret")
    assert len({first, second, third}) == 3
    assert {p["name"] for p in keychain.load_profiles()} == {first, second, third}
    assert {call.args[1] for call in simulated_keychain.set_password.call_args_list} == {first, second, third}


def test_delete_keeps_profile_on_keychain_error(simulated_keychain, caplog):
    name = keychain.save_profile("imap.example.com", 993, "user@example.com", "fake-secret")
    simulated_keychain.delete_password.side_effect = RuntimeError("denied: fake-secret")
    with pytest.raises(RuntimeError) as caught:
        keychain.delete_profile(name)
    assert "fake-secret" not in str(caught.value)
    assert "fake-secret" not in caplog.text
    assert keychain.load_profile(name) is not None


def test_delete_ignores_missing_keychain_item(simulated_keychain):
    name = keychain.save_profile("imap.example.com", 993, "user@example.com", "fake-secret")
    simulated_keychain.delete_password.side_effect = keyring.errors.PasswordDeleteError("missing")
    simulated_keychain.get_password.return_value = None
    keychain.delete_profile(name)
    assert keychain.load_profiles() == []


def test_delete_error_with_existing_password_keeps_profile(simulated_keychain):
    name = keychain.save_profile("imap.example.com", 993, "user@example.com", "fake-secret")
    simulated_keychain.delete_password.side_effect = keyring.errors.PasswordDeleteError("denied")
    simulated_keychain.get_password.return_value = "fake-secret"
    with pytest.raises(RuntimeError):
        keychain.delete_profile(name)
    assert keychain.load_profile(name) is not None


def test_delete_error_with_locked_keychain_keeps_profile(simulated_keychain):
    name = keychain.save_profile("imap.example.com", 993, "user@example.com", "fake-secret")
    simulated_keychain.delete_password.side_effect = keyring.errors.PasswordDeleteError("denied")
    simulated_keychain.get_password.side_effect = keyring.errors.KeyringLocked("locked")
    with pytest.raises(RuntimeError):
        keychain.delete_profile(name)
    assert keychain.load_profile(name) is not None


def test_failed_save_keeps_profiles(simulated_keychain):
    simulated_keychain.set_password.side_effect = RuntimeError("fake-secret")
    with pytest.raises(RuntimeError) as caught:
        keychain.save_profile("imap.example.com", 993, "user@example.com", "fake-secret")
    assert "fake-secret" not in str(caught.value)
    assert keychain.load_profiles() == []


def test_update_same_profile_keeps_one_entry(simulated_keychain):
    name = keychain.save_profile("imap.example.com", 993, "user@example.com", "first")
    keychain.save_profile("imap.example.com", 993, "user@example.com", "second")
    assert len(keychain.load_profiles()) == 1
    simulated_keychain.set_password.assert_called_with(keychain.SERVICE_NAME, name, "second")


def test_profiles_only_expose_metadata(simulated_keychain):
    from pathlib import Path
    profile = {"name": "legacy", "host": "imap.example.com", "port": 993, "username": "user@example.com", "password": "fake-secret"}
    Path(keychain.CONFIG_FILE).write_text(json.dumps([profile]))
    assert "password" not in keychain.load_profiles()[0]
    assert "password" not in keychain.load_profile("legacy")
