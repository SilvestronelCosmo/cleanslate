"""Action execution engine: RFC 8058 Unsubscribe and GDPR Art. 17 Deletion Generator."""

from typing import Dict, Any, Optional
import urllib.parse
import httpx

from cleanslate.core.models import UnsubscribeResult, GDPRRequestPayload


async def execute_one_click_unsubscribe(
    unsub_url: str,
    user_email: Optional[str] = None,
) -> UnsubscribeResult:
    """
    Execute standard RFC 8058 One-Click Unsubscribe via HTTP POST.
    RFC 8058 specifies POST with body 'List-Unsubscribe=One-Click'.
    """
    if not unsub_url or not unsub_url.startswith(("http://", "https://")):
        return UnsubscribeResult(
            success=False,
            service=unsub_url or "Unknown",
            method="rfc8058_post",
            message="URL di disiscrizione non valido o mancante.",
        )
        
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "CleanSlate-Unsubscriber/1.0",
    }
    data = "List-Unsubscribe=One-Click"
    
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            resp = await client.post(unsub_url, data=data, headers=headers)
            
            # RFC 8058 specifies 2xx status code on success
            if 200 <= resp.status_code < 300:
                return UnsubscribeResult(
                    success=True,
                    service=unsub_url,
                    method="rfc8058_post",
                    message="Disiscrizione completata con successo tramite protocollo standard RFC 8058.",
                    details={"status_code": resp.status_code},
                )
            
            # Fallback: some services handle GET on the unsubscribe link
            resp_get = await client.get(unsub_url, headers=headers)
            if 200 <= resp_get.status_code < 300:
                return UnsubscribeResult(
                    success=True,
                    service=unsub_url,
                    method="http_get_fallback",
                    message="Disiscrizione eseguita tramite richiesta HTTP diretta.",
                    details={"status_code": resp_get.status_code},
                )
                
            return UnsubscribeResult(
                success=False,
                service=unsub_url,
                method="rfc8058_post",
                message=f"Il server ha risposto con codice HTTP {resp.status_code}.",
                details={"status_code": resp.status_code},
            )
    except Exception as e:
        return UnsubscribeResult(
            success=False,
            service=unsub_url,
            method="rfc8058_post",
            message=f"Errore durante l'invio della richiesta: {str(e)}",
            details={"error": str(e)},
        )


def generate_gdpr_deletion_request(payload: GDPRRequestPayload) -> Dict[str, Any]:
    """
    Generate an authoritative GDPR Article 17 (Right to Erasure) request.
    Returns subject, plain text body, and ready-to-click mailto: URI.
    """
    name = payload.user_name.strip()
    email = payload.user_email.strip()
    service = payload.service_name.strip()
    dpo = (payload.dpo_email or "privacy@" + service.lower().replace(" ", "") + ".com").strip()
    
    if payload.language.lower() == "it":
        subject = f"Richiesta di cancellazione dati personali ex Art. 17 GDPR - {name} ({email})"
        body = f"""Gentile Responsabile della Protezione dei Dati (DPO) / Ufficio Privacy di {service},

Il/La sottoscritto/a {name}, titolare dell'account associato all'indirizzo email:
{email}

con la presente esercita formalmente il proprio DIRITTO ALLA CANCELLAZIONE (Diritto all'oblio) ai sensi dell'Articolo 17 del Regolamento UE 2016/679 (GDPR).

Richiedo espressamente e senza ingiustificato ritardo:
1. La chiusura e cancellazione definitiva dell'account utente associato a {service}.
2. La cancellazione integrale di tutti i dati personali, record di utilizzo, backup e metadati trattati.
3. La revoca immediata di qualsiasi consenso prestato a fini di marketing, profilazione o comunicazione a terzi.
4. La notifica dell'avvenuta cancellazione a tutti i destinatari a cui sono stati trasmessi i miei dati, ai sensi dell'Articolo 19 del GDPR.

Vi ricordo che, ai sensi dell'Articolo 12, paragrafo 3 del GDPR, avete l'obbligo legale di fornire riscontro a questa richiesta al più tardi entro un mese dal ricevimento della presente.

In attesa di una Vostra tempestiva conferma scritta dell'avvenuta cancellazione.

Cordiali saluti,

{name}
{email}
"""
    else:
        subject = f"GDPR Article 17 Erasure Request - {name} ({email})"
        body = f"""To the Data Protection Officer (DPO) / Privacy Team at {service},

I am writing to formally exercise my Right to Erasure ('Right to be Forgotten') pursuant to Article 17 of the General Data Protection Regulation (EU) 2016/679 (GDPR).

User Details:
Name: {name}
Registered Email: {email}

I hereby request without undue delay:
1. The permanent deletion and closure of my account with {service}.
2. The complete erasure of all my personal data, usage history, backups, and profile records.
3. Immediate revocation of any consent granted for direct marketing or data sharing with third parties.
4. Notification of this erasure to each recipient to whom the personal data has been disclosed, pursuant to Article 19 GDPR.

As specified under Article 12(3) GDPR, you are legally required to provide confirmation of this erasure within 30 calendar days.

Please confirm receipt of this request and provide written notice once the erasure is complete.

Sincerely,

{name}
{email}
"""

    # Build mailto URI
    params = {
        "subject": subject,
        "body": body,
    }
    mailto_uri = f"mailto:{dpo}?{urllib.parse.urlencode(params, quote_via=urllib.parse.quote)}"
    
    return {
        "service": service,
        "dpo_email": dpo,
        "subject": subject,
        "body": body,
        "mailto_uri": mailto_uri,
    }
