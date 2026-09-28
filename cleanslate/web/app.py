"""FastAPI Web Application and API routes for CleanSlate."""

import os
import shutil
import tempfile
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from cleanslate.core.models import (
    ScanSummary,
    ServiceEntry,
    ServiceCategory,
    DeletionDifficulty,
    UnsubscribeResult,
    GDPRRequestPayload,
)
from cleanslate.core.directory import SERVICES_DATABASE, lookup_service
from cleanslate.core.osint import run_osint_scan
from cleanslate.core.imap_scanner import scan_imap_inbox, scan_mbox_file
from cleanslate.core.actions import (
    execute_one_click_unsubscribe,
    generate_gdpr_deletion_request,
)

app = FastAPI(
    title="CleanSlate API",
    description="Local-First Digital Footprint Audit & Unsubscriber",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class OSINTScanRequest(BaseModel):
    email: str


class IMAPScanRequest(BaseModel):
    host: str = "imap.gmail.com"
    port: int = 993
    username: str
    password: str
    max_emails: int = 150


class UnsubscribeRequest(BaseModel):
    unsub_url: str
    email: Optional[str] = None


@app.get("/")
async def root():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "CleanSlate API running. Open /docs for Swagger UI."}


@app.post("/api/scan/osint", response_model=ScanSummary)
async def scan_osint_endpoint(req: OSINTScanRequest):
    """Run non-intrusive asynchronous OSINT probes against the email address."""
    email = req.email.strip()
    if "@" not in email or "." not in email:
        raise HTTPException(status_code=400, detail="Indirizzo email non valido.")

    found_services = await run_osint_scan(email)

    summary = ScanSummary(
        target_email=email,
        total_services=len(found_services),
        accounts_count=sum(1 for s in found_services if s.category == ServiceCategory.ACCOUNT),
        subscriptions_count=sum(1 for s in found_services if s.category == ServiceCategory.SUBSCRIPTION),
        newsletters_count=sum(1 for s in found_services if s.category == ServiceCategory.NEWSLETTER),
        breaches_count=sum(1 for s in found_services if s.category == ServiceCategory.BREACH),
        services=found_services,
    )
    return summary


@app.post("/api/scan/imap", response_model=ScanSummary)
async def scan_imap_endpoint(req: IMAPScanRequest):
    """Perform real-time IMAP header scan without downloading message bodies."""
    try:
        summary = scan_imap_inbox(
            host=req.host,
            port=req.port,
            username=req.username,
            password=req.password,
            max_emails=req.max_emails,
        )
        return summary
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Errore connessione IMAP: {str(e)}. Verifica host, porta e password applicativa.",
        )


@app.post("/api/scan/mbox", response_model=ScanSummary)
async def scan_mbox_endpoint(file: UploadFile = File(...)):
    """Upload and audit local .mbox or .eml export file completely offline."""
    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, file.filename or "export.mbox")
    
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        services = scan_mbox_file(temp_path)
        return ScanSummary(
            target_email=file.filename or "offline-export",
            total_services=len(services),
            accounts_count=sum(1 for s in services if s.category == ServiceCategory.ACCOUNT),
            subscriptions_count=sum(1 for s in services if s.category == ServiceCategory.SUBSCRIPTION),
            newsletters_count=sum(1 for s in services if s.category == ServiceCategory.NEWSLETTER),
            breaches_count=sum(1 for s in services if s.category == ServiceCategory.BREACH),
            services=services,
        )
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@app.post("/api/actions/unsubscribe", response_model=UnsubscribeResult)
async def unsubscribe_endpoint(req: UnsubscribeRequest):
    """Trigger RFC 8058 one-click HTTP POST unsubscription."""
    return await execute_one_click_unsubscribe(req.unsub_url, req.email)


@app.post("/api/actions/gdpr-template")
async def gdpr_template_endpoint(payload: GDPRRequestPayload):
    """Generate pre-filled, legally structured GDPR Article 17 erasure request."""
    return generate_gdpr_deletion_request(payload)


@app.get("/api/directory")
async def directory_endpoint(q: Optional[str] = None):
    """Search the integrated JustDelete.me directory."""
    if not q:
        return list(SERVICES_DATABASE.values())
    
    q_clean = q.lower().strip()
    matches = [
        item for item in SERVICES_DATABASE.values()
        if q_clean in item["name"].lower() or q_clean in item["domain"].lower()
    ]
    return matches


@app.get("/api/demo-data", response_model=ScanSummary)
async def demo_data_endpoint(email: str = "alex.rossi@example.com"):
    """Portfolio Showcase: Returns a realistic multi-service digital footprint scan."""
    mock_services = [
        ServiceEntry(
            name="Spotify",
            domain="spotify.com",
            category=ServiceCategory.SUBSCRIPTION,
            found_via="inbox_receipt",
            difficulty=DeletionDifficulty.EASY,
            delete_url="https://support.spotify.com/article/close-account/",
            dpo_email="privacy@spotify.com",
            notes="Piano Premium attivo rilevato da ricevuta mensile di €10.99.",
            last_activity="24 Set 2026",
            details={"plan": "Premium Individual", "amount": "€10.99/mo"},
        ),
        ServiceEntry(
            name="Netflix",
            domain="netflix.com",
            category=ServiceCategory.SUBSCRIPTION,
            found_via="inbox_receipt",
            difficulty=DeletionDifficulty.MEDIUM,
            delete_url="https://www.netflix.com/account/delete",
            dpo_email="privacy@netflix.com",
            notes="Rinnovo automatico attivo.",
            last_activity="18 Set 2026",
            details={"plan": "Standard HD"},
        ),
        ServiceEntry(
            name="Substack",
            domain="substack.com",
            category=ServiceCategory.NEWSLETTER,
            found_via="inbox_unsubscribe",
            difficulty=DeletionDifficulty.EASY,
            delete_url="https://substack.com/account/settings",
            dpo_email="privacy@substack.com",
            unsubscribe_url="https://substack.com/api/v1/unsubscribe-demo",
            unsubscribe_post=True,
            last_activity="Ieri, 16:42",
            details={"newsletter": "Tech Leaders Weekly"},
        ),
        ServiceEntry(
            name="Canva",
            domain="canva.com",
            category=ServiceCategory.ACCOUNT,
            found_via="inbox_welcome",
            difficulty=DeletionDifficulty.EASY,
            delete_url="https://www.canva.com/settings/account",
            dpo_email="privacy@canva.com",
            notes="Account registrato via email confirmation.",
            last_activity="12 Ago 2025",
        ),
        ServiceEntry(
            name="GitHub",
            domain="github.com",
            category=ServiceCategory.ACCOUNT,
            found_via="osint",
            difficulty=DeletionDifficulty.EASY,
            delete_url="https://github.com/settings/admin",
            dpo_email="privacy@github.com",
            notes="Profilo pubblico rilevato tramite endpoint API GitHub.",
            last_activity="Attivo",
            details={"username": "alexrossi-dev"},
        ),
        ServiceEntry(
            name="Medium",
            domain="medium.com",
            category=ServiceCategory.NEWSLETTER,
            found_via="inbox_unsubscribe",
            difficulty=DeletionDifficulty.EASY,
            delete_url="https://medium.com/me/settings/security",
            dpo_email="yourfriends@medium.com",
            unsubscribe_url="https://medium.com/unsubscribe-demo",
            unsubscribe_post=False,
            last_activity="3 giorni fa",
        ),
        ServiceEntry(
            name="Deliveroo",
            domain="deliveroo.com",
            category=ServiceCategory.ACCOUNT,
            found_via="inbox_welcome",
            difficulty=DeletionDifficulty.EASY,
            delete_url="https://deliveroo.it/it/account",
            dpo_email="dpo@deliveroo.com",
            notes="Account cliente registrato.",
            last_activity="05 Lug 2026",
        ),
        ServiceEntry(
            name="Adobe",
            domain="adobe.com",
            category=ServiceCategory.ACCOUNT,
            found_via="osint",
            difficulty=DeletionDifficulty.HARD,
            delete_url="https://account.adobe.com/privacy",
            dpo_email="dpo@adobe.com",
            notes="Adobe ID attivo rilevato. Richiede disdetta piani cloud prima della rimozione.",
            last_activity="Rilevato OSINT",
        ),
    ]

    return ScanSummary(
        target_email=email,
        total_services=len(mock_services),
        accounts_count=sum(1 for s in mock_services if s.category == ServiceCategory.ACCOUNT),
        subscriptions_count=sum(1 for s in mock_services if s.category == ServiceCategory.SUBSCRIPTION),
        newsletters_count=sum(1 for s in mock_services if s.category == ServiceCategory.NEWSLETTER),
        breaches_count=0,
        services=mock_services,
    )
