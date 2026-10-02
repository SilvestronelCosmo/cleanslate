"""Require server verification before any mailbox credentials are sent."""

import ssl
from unittest.mock import Mock
import pytest
from cleanslate.core import imap_scanner


def test_imap_requires_certificate_and_hostname(monkeypatch):
    mail = Mock()
    mail.search.return_value = ("OK", [b""])
    factory = Mock(return_value=mail)
    monkeypatch.setattr(imap_scanner.imaplib, "IMAP4_SSL", factory)
    result = imap_scanner.scan_imap_inbox("imap.example.com", 993, "demo@example.com", "dummy")
    context = factory.call_args.kwargs["ssl_context"]
    assert context.verify_mode == ssl.CERT_REQUIRED
    assert context.check_hostname is True
    assert context.cert_store_stats()["x509_ca"] > 0
    assert result.total_services == 0
    mail.login.assert_called_once_with("demo@example.com", "dummy")


def test_certificate_error_stops_before_login(monkeypatch):
    mail = Mock()
    factory = Mock(side_effect=ssl.SSLCertVerificationError("test certificate rejected"), return_value=mail)
    monkeypatch.setattr(imap_scanner.imaplib, "IMAP4_SSL", factory)
    with pytest.raises(ssl.SSLCertVerificationError):
        imap_scanner.scan_imap_inbox("imap.example.com", 993, "demo@example.com", "dummy")
    mail.login.assert_not_called()
