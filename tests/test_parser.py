"""Tests for email header parsing and classification."""

import email
from cleanslate.core.imap_scanner import (
    decode_mime_header,
    parse_sender,
    parse_unsubscribe_header,
    analyze_message_headers,
)
from cleanslate.core.models import ServiceCategory


def test_parse_sender():
    name, domain = parse_sender('"Spotify Support" <no-reply@spotify.com>')
    assert name == "Spotify Support"
    assert domain == "spotify.com"

    name, domain = parse_sender("news@substack.com")
    assert "substack.com" in domain


def test_parse_unsubscribe_header():
    header = "<https://newsletter.example.com/unsub?id=123>, <mailto:unsub@example.com?subject=unsub>"
    http_url, mailto_url = parse_unsubscribe_header(header)
    assert http_url == "https://newsletter.example.com/unsub?id=123"
    assert mailto_url == "mailto:unsub@example.com?subject=unsub"


def test_classify_welcome_email():
    raw_email = """From: Canva <welcome@canva.com>
To: test@example.com
Subject: Benvenuto in Canva! Conferma la tua email
Date: Mon, 28 Sep 2026 12:00:00 +0200

Hello
"""
    msg = email.message_from_string(raw_email)
    entry = analyze_message_headers(msg)
    assert entry is not None
    assert entry.category == ServiceCategory.ACCOUNT
    assert entry.domain == "canva.com"
    assert entry.name == "Canva"


def test_classify_billing_email():
    raw_email = """From: Netflix Billing <info@mailer.netflix.com>
To: test@example.com
Subject: Your receipt from Netflix for September
Date: Mon, 28 Sep 2026 12:00:00 +0200

Payment confirmed
"""
    msg = email.message_from_string(raw_email)
    entry = analyze_message_headers(msg)
    assert entry is not None
    assert entry.category == ServiceCategory.SUBSCRIPTION
    assert entry.name == "Netflix"


def test_classify_newsletter_email():
    raw_email = """From: Tech Digest <editor@techdigest.com>
To: test@example.com
Subject: Weekly engineering highlights
List-Unsubscribe: <https://techdigest.com/unsub/42>
List-Unsubscribe-Post: List-Unsubscribe=One-Click
Date: Mon, 28 Sep 2026 12:00:00 +0200

Newsletter body
"""
    msg = email.message_from_string(raw_email)
    entry = analyze_message_headers(msg)
    assert entry is not None
    assert entry.category == ServiceCategory.NEWSLETTER
    assert entry.unsubscribe_url == "https://techdigest.com/unsub/42"
    assert entry.unsubscribe_post is True
