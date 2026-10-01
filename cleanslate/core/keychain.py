"""IMAP profile metadata and passwords stored in the macOS Keychain."""

import json
import os
from sys import platform
from typing import Any, Dict, List, Optional

import keyring
from keyring.backends import macOS

SERVICE_NAME = "com.cleanslate.imap"
CONFIG_DIR = os.path.expanduser("~/.cleanslate")
CONFIG_FILE = os.path.join(CONFIG_DIR, "profiles.json")


def _keyring_backend():
    if platform != "darwin":
        raise RuntimeError("I profili con password richiedono il Portachiavi di macOS.")
    return macOS.Keyring()


def _load_config() -> List[Dict[str, Any]]:
    """Load only profile metadata; a corrupt file must not be overwritten."""
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            profiles = json.load(f)
    except FileNotFoundError:
        return []
    fields = ("name", "host", "port", "username")
    return [{field: profile[field] for field in fields} for profile in profiles]


def _save_config(profiles: List[Dict[str, Any]]) -> None:
    """Save profile metadata without passwords."""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(profiles, f, indent=2)


def save_profile(host: str, port: int, username: str, password: str) -> str:
    """Save metadata and the password, returning the canonical profile ID."""
    host = host.strip().lower()
    username = username.strip()
    name = f"{username}@{host}:{port}".lower()
    profile = {"name": name, "host": host, "port": port, "username": username}
    profiles = _load_config()
    try:
        _keyring_backend().set_password(SERVICE_NAME, name, password)
    except Exception:
        raise RuntimeError("Impossibile salvare la password nel Portachiavi.") from None

    profiles = [p for p in profiles if p["name"] != name]
    profiles.append(profile)
    _save_config(profiles)
    return name


def load_profiles() -> List[Dict[str, Any]]:
    """Return all profiles without passwords."""
    return _load_config()


def load_profile(name: str) -> Optional[Dict[str, Any]]:
    """Return a single profile without its password."""
    return next((p for p in _load_config() if p["name"] == name), None)


def get_password(name: str) -> Optional[str]:
    """Read a password for internal use only; never include it in errors."""
    try:
        return _keyring_backend().get_password(SERVICE_NAME, name)
    except Exception:
        raise RuntimeError("Impossibile leggere la password dal Portachiavi.") from None


def delete_profile(name: str) -> None:
    """Delete metadata only after the password is deleted or confirmed absent."""
    profiles = _load_config()
    try:
        backend = _keyring_backend()
        try:
            backend.delete_password(SERVICE_NAME, name)
        except keyring.errors.PasswordDeleteError:
            if backend.get_password(SERVICE_NAME, name) is not None:
                raise RuntimeError("Password ancora presente.") from None
    except Exception:
        raise RuntimeError("Impossibile eliminare la password dal Portachiavi.") from None

    _save_config([p for p in profiles if p["name"] != name])
