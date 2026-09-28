"""Email inbox scanner via IMAP and offline MBOX/EML parsers."""

import email
from email.header import decode_header
import imaplib
import mailbox
import re
from typing import Dict, Generator, List, Optional, Tuple
from cleanslate.core.models import (
    ServiceEntry,
    ServiceCategory,
    DeletionDifficulty,
    ScanSummary,
)
from cleanslate.core.directory import lookup_service, normalize_domain

# Heuristic keyword patterns (Multilingual: EN & IT)
WELCOME_PATTERNS = [
    r"welcome to",
    r"welcome aboard",
    r"benvenut[oa] (su|in|a)?",
    r"confirm (your )?(email|account|registration)",
    r"conferma (la tua )?(email|registrazione|account)",
    r"verify (your )?(email|account)",
    r"verifica (la tua )?(email|account)",
    r"attiva (il tuo )?account",
    r"activate (your )?account",
    r"registration (successful|confirmed)",
    r"registrazione (completata|avvenuta)",
    r"your new account",
    r"creazione account",
    r"grazie per esserti registrat[oa]",
    r"thanks for signing up",
]

BILLING_PATTERNS = [
    r"receipt (for|from)",
    r"ricevuta (di pagamento|per)",
    r"your invoice",
    r"fattura (elettronica|n\.)",
    r"subscription (confirmed|renewed|active)",
    r"abbonamento (confermato|rinnovato|attivo)",
    r"payment (received|confirmed|processed)",
    r"pagamento (ricevuto|confermato|effettuato)",
    r"rinnovo (automatico|annuale|mensile)",
    r"your membership",
    r"stripe payment",
    r"ordine confermato",
    r"order confirmation",
]


def decode_mime_header(header_val: Optional[str]) -> str:
    """Safely decode MIME encoded header text."""
    if not header_val:
        return ""
    decoded_fragments = []
    try:
        parts = decode_header(header_val)
        for content, encoding in parts:
            if isinstance(content, bytes):
                decoded_fragments.append(content.decode(encoding or "utf-8", errors="replace"))
            else:
                decoded_fragments.append(str(content))
        return "".join(decoded_fragments).strip()
    except Exception:
        return str(header_val).strip()


def parse_sender(from_header: str) -> Tuple[str, str]:
    """Extract display name and email domain from a From header."""
    decoded = decode_mime_header(from_header)
    match = re.search(r"<([^>]+)>", decoded)
    if match:
        email_addr = match.group(1).strip()
        name = decoded.replace(match.group(0), "").replace('"', '').strip()
    else:
        email_addr = decoded.strip()
        name = decoded.split("@")[0].strip()
        
    domain = normalize_domain(email_addr)
    clean_name = name or domain.split(".")[0].capitalize()
    return clean_name, domain


def parse_unsubscribe_header(header_val: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """
    Parse RFC 2369 List-Unsubscribe header.
    Returns (http_url, mailto_url).
    """
    if not header_val:
        return None, None
        
    http_url = None
    mailto_url = None
    
    # Items are enclosed in <...>
    items = re.findall(r"<([^>]+)>", header_val)
    for item in items:
        item = item.strip()
        if item.startswith("http://") or item.startswith("https://"):
            if not http_url:
                http_url = item
        elif item.startswith("mailto:"):
            if not mailto_url:
                mailto_url = item
                
    return http_url, mailto_url


def analyze_message_headers(
    msg: email.message.Message,
) -> Optional[ServiceEntry]:
    """Analyze email headers and classify service entry."""
    from_header = msg.get("From", "")
    if not from_header:
        return None
        
    sender_name, domain = parse_sender(from_header)
    subject = decode_mime_header(msg.get("Subject", "")).lower()
    date_header = decode_mime_header(msg.get("Date", ""))
    
    unsub_header = msg.get("List-Unsubscribe")
    unsub_post_header = msg.get("List-Unsubscribe-Post", "")
    unsub_url, unsub_mailto = parse_unsubscribe_header(unsub_header)
    supports_rfc8058 = "List-Unsubscribe=One-Click" in unsub_post_header
    
    # Check directory for metadata
    service_info = lookup_service(domain) or lookup_service(sender_name) or {}
    final_name = service_info.get("name") or sender_name
    difficulty = service_info.get("difficulty", DeletionDifficulty.UNKNOWN)
    delete_url = service_info.get("delete_url")
    dpo_email = service_info.get("dpo_email")
    notes = service_info.get("notes")
    
    # 1. Billing / Subscription check
    for pat in BILLING_PATTERNS:
        if re.search(pat, subject, re.IGNORECASE):
            return ServiceEntry(
                name=final_name,
                domain=domain,
                category=ServiceCategory.SUBSCRIPTION,
                found_via="inbox_receipt",
                difficulty=difficulty,
                delete_url=delete_url,
                dpo_email=dpo_email,
                notes=notes,
                last_activity=date_header,
                details={"subject": subject},
            )
            
    # 2. Account registration / Welcome check
    for pat in WELCOME_PATTERNS:
        if re.search(pat, subject, re.IGNORECASE):
            return ServiceEntry(
                name=final_name,
                domain=domain,
                category=ServiceCategory.ACCOUNT,
                found_via="inbox_welcome",
                difficulty=difficulty,
                delete_url=delete_url,
                dpo_email=dpo_email,
                notes=notes,
                last_activity=date_header,
                details={"subject": subject},
            )
            
    # 3. Newsletter / Mailing List check
    if unsub_url or unsub_mailto:
        return ServiceEntry(
            name=final_name,
            domain=domain,
            category=ServiceCategory.NEWSLETTER,
            found_via="inbox_unsubscribe",
            difficulty=difficulty,
            delete_url=delete_url,
            dpo_email=dpo_email,
            notes=notes,
            unsubscribe_url=unsub_url,
            unsubscribe_mailto=unsub_mailto,
            unsubscribe_post=supports_rfc8058,
            last_activity=date_header,
            details={"subject": subject},
        )
        
    return None


def scan_mbox_file(mbox_path: str, max_messages: int = 500) -> List[ServiceEntry]:
    """Scan a local .mbox file (e.g. from Google Takeout or Thunderbird)."""
    results_map: Dict[str, ServiceEntry] = {}
    box = mailbox.mbox(mbox_path)
    
    count = 0
    for key in box.iterkeys():
        if count >= max_messages:
            break
        try:
            msg = box.get_message(key)
            entry = analyze_message_headers(msg)
            if entry:
                # Merge or keep most relevant
                key_id = f"{entry.domain}:{entry.category.value}"
                if key_id not in results_map:
                    results_map[key_id] = entry
            count += 1
        except Exception:
            continue
            
    return list(results_map.values())


def scan_imap_inbox(
    host: str,
    port: int,
    username: str,
    password: str,
    folder: str = "INBOX",
    max_emails: int = 250,
) -> ScanSummary:
    """Connect to IMAP server, fetch headers, and classify services."""
    mail = imaplib.IMAP4_SSL(host, port)
    mail.login(username, password)
    mail.select(folder, readonly=True)
    
    status, messages = mail.search(None, "ALL")
    if status != "OK":
        mail.close()
        mail.logout()
        return ScanSummary(target_email=username)
        
    msg_ids = messages[0].split()
    # Take latest messages first
    msg_ids = msg_ids[-max_emails:] if len(msg_ids) > max_emails else msg_ids
    msg_ids.reverse()
    
    results_map: Dict[str, ServiceEntry] = {}
    
    # Fetch headers only: efficient and bandwidth-friendly
    header_fields = "(BODY.PEEK[HEADER.FIELDS (FROM TO SUBJECT DATE LIST-UNSUBSCRIBE LIST-UNSUBSCRIBE-POST)])"
    
    for mid in msg_ids:
        try:
            res, data = mail.fetch(mid, header_fields)
            if res != "OK" or not data:
                continue
            raw_header = data[0][1]
            msg = email.message_from_bytes(raw_header)
            entry = analyze_message_headers(msg)
            if entry:
                key_id = f"{entry.domain}:{entry.category.value}"
                if key_id not in results_map:
                    results_map[key_id] = entry
        except Exception:
            continue
            
    mail.close()
    mail.logout()
    
    services = list(results_map.values())
    summary = ScanSummary(
        target_email=username,
        total_services=len(services),
        accounts_count=sum(1 for s in services if s.category == ServiceCategory.ACCOUNT),
        subscriptions_count=sum(1 for s in services if s.category == ServiceCategory.SUBSCRIPTION),
        newsletters_count=sum(1 for s in services if s.category == ServiceCategory.NEWSLETTER),
        breaches_count=sum(1 for s in services if s.category == ServiceCategory.BREACH),
        services=services,
    )
    return summary
