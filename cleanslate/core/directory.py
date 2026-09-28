"""Service directory with direct deletion links, difficulty ratings, and DPO contacts."""

from typing import Dict, Optional, Any
from cleanslate.core.models import DeletionDifficulty

# Comprehensive catalog based on JustDelete.me patterns and privacy compliance registries
SERVICES_DATABASE: Dict[str, Dict[str, Any]] = {
    "spotify.com": {
        "name": "Spotify",
        "domain": "spotify.com",
        "difficulty": DeletionDifficulty.EASY,
        "delete_url": "https://support.spotify.com/article/close-account/",
        "dpo_email": "privacy@spotify.com",
        "notes": "Se hai un piano Premium, devi prima annullare l'abbonamento.",
    },
    "netflix.com": {
        "name": "Netflix",
        "domain": "netflix.com",
        "difficulty": DeletionDifficulty.MEDIUM,
        "delete_url": "https://www.netflix.com/account/delete",
        "dpo_email": "privacy@netflix.com",
        "notes": "Gli account disattivati vengono eliminati automaticamente dopo 10 mesi oppure subito inviando richiesta privacy.",
    },
    "amazon.com": {
        "name": "Amazon",
        "domain": "amazon.com",
        "difficulty": DeletionDifficulty.HARD,
        "delete_url": "https://www.amazon.it/hz/contact-us/foresight/hub-dcp-close-account",
        "dpo_email": "eu-privacy@amazon.it",
        "notes": "Richiede conferma in due passaggi e chiude tutti i servizi associati (Audible, Kindle, Prime).",
    },
    "amazon.it": {
        "name": "Amazon Italia",
        "domain": "amazon.it",
        "difficulty": DeletionDifficulty.HARD,
        "delete_url": "https://www.amazon.it/hz/contact-us/foresight/hub-dcp-close-account",
        "dpo_email": "eu-privacy@amazon.it",
        "notes": "Richiede conferma via SMS/email e revoca l'accesso a tutti i servizi AWS/Prime.",
    },
    "twitter.com": {
        "name": "X (Twitter)",
        "domain": "twitter.com",
        "difficulty": DeletionDifficulty.EASY,
        "delete_url": "https://x.com/settings/deactivate",
        "dpo_email": "dpo@x.com",
        "notes": "Account disattivato per 30 giorni prima della cancellazione definitiva.",
    },
    "x.com": {
        "name": "X (Twitter)",
        "domain": "x.com",
        "difficulty": DeletionDifficulty.EASY,
        "delete_url": "https://x.com/settings/deactivate",
        "dpo_email": "dpo@x.com",
        "notes": "Account disattivato per 30 giorni prima della cancellazione definitiva.",
    },
    "github.com": {
        "name": "GitHub",
        "domain": "github.com",
        "difficulty": DeletionDifficulty.EASY,
        "delete_url": "https://github.com/settings/admin",
        "dpo_email": "privacy@github.com",
        "notes": "Eliminazione immediata in Settings > Account > Delete account.",
    },
    "reddit.com": {
        "name": "Reddit",
        "domain": "reddit.com",
        "difficulty": DeletionDifficulty.EASY,
        "delete_url": "https://www.reddit.com/settings",
        "dpo_email": "privacy@reddit.com",
        "notes": "Disattivazione definitiva in fondo alla schermata Impostazioni Utente.",
    },
    "linkedin.com": {
        "name": "LinkedIn",
        "domain": "linkedin.com",
        "difficulty": DeletionDifficulty.EASY,
        "delete_url": "https://www.linkedin.com/help/linkedin/answer/a1339363",
        "dpo_email": "linkedin_dpo@linkedin.com",
        "notes": "Impostazioni > Preferenze account > Gestione account > Chiudi account.",
    },
    "facebook.com": {
        "name": "Facebook",
        "domain": "facebook.com",
        "difficulty": DeletionDifficulty.MEDIUM,
        "delete_url": "https://www.facebook.com/help/delete_account",
        "dpo_email": "dpo@facebook.com",
        "notes": "Meta applica un periodo di grazia di 30 giorni durante il quale il login ripristina l'account.",
    },
    "instagram.com": {
        "name": "Instagram",
        "domain": "instagram.com",
        "difficulty": DeletionDifficulty.MEDIUM,
        "delete_url": "https://www.instagram.com/accounts/remove/request/permanent/",
        "dpo_email": "dpo@instagram.com",
        "notes": "Gestito tramite Meta Accounts Center con periodo di grazia di 30 giorni.",
    },
    "tiktok.com": {
        "name": "TikTok",
        "domain": "tiktok.com",
        "difficulty": DeletionDifficulty.MEDIUM,
        "delete_url": "https://support.tiktok.com/it/account-and-privacy/deleting-an-account",
        "dpo_email": "privacy@tiktok.com",
        "notes": "Disattivazione per 30 giorni prima della cancellazione permanente.",
    },
    "discord.com": {
        "name": "Discord",
        "domain": "discord.com",
        "difficulty": DeletionDifficulty.EASY,
        "delete_url": "https://support.discord.com/hc/en-us/articles/212500838-How-do-I-delete-my-account",
        "dpo_email": "privacy@discord.com",
        "notes": "Richiede il trasferimento di proprietà dei server creati prima di consentire la cancellazione.",
    },
    "slack.com": {
        "name": "Slack",
        "domain": "slack.com",
        "difficulty": DeletionDifficulty.HARD,
        "delete_url": "https://my.slack.com/account/settings",
        "dpo_email": "dpo@slack.com",
        "notes": "La cancellazione dell'utente dipende dai criteri di conservazione del workspace aziendale.",
    },
    "notion.so": {
        "name": "Notion",
        "domain": "notion.so",
        "difficulty": DeletionDifficulty.EASY,
        "delete_url": "https://www.notion.so/my-account",
        "dpo_email": "privacy@makenotion.com",
        "notes": "Impostazioni > Il mio account > Elimina il mio account.",
    },
    "dropbox.com": {
        "name": "Dropbox",
        "domain": "dropbox.com",
        "difficulty": DeletionDifficulty.EASY,
        "delete_url": "https://www.dropbox.com/account/delete",
        "dpo_email": "privacy@dropbox.com",
        "notes": "Elimina i file cloud e le sincronizzazioni entro 30-60 giorni.",
    },
    "adobe.com": {
        "name": "Adobe",
        "domain": "adobe.com",
        "difficulty": DeletionDifficulty.HARD,
        "delete_url": "https://account.adobe.com/privacy",
        "dpo_email": "dpo@adobe.com",
        "notes": "Richiede l'annullamento di tutti gli abbonamenti Creative Cloud attivi con possibili penali.",
    },
    "canva.com": {
        "name": "Canva",
        "domain": "canva.com",
        "difficulty": DeletionDifficulty.EASY,
        "delete_url": "https://www.canva.com/settings/account",
        "dpo_email": "privacy@canva.com",
        "notes": "Impostazioni account > Accesso e sicurezza > Elimina account.",
    },
    "duolingo.com": {
        "name": "Duolingo",
        "domain": "duolingo.com",
        "difficulty": DeletionDifficulty.EASY,
        "delete_url": "https://drive-thru.duolingo.com/",
        "dpo_email": "privacy@duolingo.com",
        "notes": "Portale dedicato Drive-Thru per l'eliminazione dei dati.",
    },
    "pinterest.com": {
        "name": "Pinterest",
        "domain": "pinterest.com",
        "difficulty": DeletionDifficulty.EASY,
        "delete_url": "https://www.pinterest.com/settings/account-settings/",
        "dpo_email": "privacy-support@pinterest.com",
        "notes": "Disattivazione immediata, cancellazione permanente dopo 14 giorni.",
    },
    "uber.com": {
        "name": "Uber",
        "domain": "uber.com",
        "difficulty": DeletionDifficulty.MEDIUM,
        "delete_url": "https://myprivacy.uber.com/",
        "dpo_email": "privacy@uber.com",
        "notes": "Disattiva sia Uber che Uber Eats con periodo di grazia di 30 giorni.",
    },
    "airbnb.com": {
        "name": "Airbnb",
        "domain": "airbnb.com",
        "difficulty": DeletionDifficulty.MEDIUM,
        "delete_url": "https://www.airbnb.it/help/article/240",
        "dpo_email": "dpo@airbnb.com",
        "notes": "Impossibile eliminare se ci sono prenotazioni attive o pagamenti in sospeso.",
    },
    "medium.com": {
        "name": "Medium",
        "domain": "medium.com",
        "difficulty": DeletionDifficulty.EASY,
        "delete_url": "https://medium.com/me/settings/security",
        "dpo_email": "yourfriends@medium.com",
        "notes": "Impostazioni > Security and apps > Delete account.",
    },
    "substack.com": {
        "name": "Substack",
        "domain": "substack.com",
        "difficulty": DeletionDifficulty.EASY,
        "delete_url": "https://substack.com/account/settings",
        "dpo_email": "privacy@substack.com",
        "notes": "Impostazioni account > Delete Account.",
    },
    "steam": {
        "name": "Steam",
        "domain": "steampowered.com",
        "difficulty": DeletionDifficulty.HARD,
        "delete_url": "https://help.steampowered.com/it/faqs/view/4593-5CB7-DC3C-64F0",
        "dpo_email": "questions@valvesoftware.com",
        "notes": "Richiede ticket al supporto clienti Valve e prova di proprietà dei giochi.",
    },
    "steampowered.com": {
        "name": "Steam",
        "domain": "steampowered.com",
        "difficulty": DeletionDifficulty.HARD,
        "delete_url": "https://help.steampowered.com/it/faqs/view/4593-5CB7-DC3C-64F0",
        "dpo_email": "questions@valvesoftware.com",
        "notes": "Richiede ticket al supporto clienti Valve e prova di proprietà dei giochi.",
    },
    "paypal.com": {
        "name": "PayPal",
        "domain": "paypal.com",
        "difficulty": DeletionDifficulty.MEDIUM,
        "delete_url": "https://www.paypal.com/myaccount/settings",
        "dpo_email": "dpo@paypal.com",
        "notes": "Richiede saldo a zero e assenza di transazioni o contestazioni in sospeso.",
    },
    "stripe.com": {
        "name": "Stripe",
        "domain": "stripe.com",
        "difficulty": DeletionDifficulty.MEDIUM,
        "delete_url": "https://dashboard.stripe.com/settings/user",
        "dpo_email": "privacy@stripe.com",
        "notes": "La cancellazione dell'account commerciante è soggetta alle normative antiriciclaggio.",
    },
    "deliveroo.com": {
        "name": "Deliveroo",
        "domain": "deliveroo.com",
        "difficulty": DeletionDifficulty.EASY,
        "delete_url": "https://deliveroo.it/it/account",
        "dpo_email": "dpo@deliveroo.com",
        "notes": "Disponibile direttamente nelle impostazioni account dell'app o via web.",
    },
    "justeat.it": {
        "name": "Just Eat",
        "domain": "justeat.it",
        "difficulty": DeletionDifficulty.MEDIUM,
        "delete_url": "https://www.justeat.it/help/article/360000889218",
        "dpo_email": "privacy@justeattakeaway.com",
        "notes": "Richiede richiesta tramite form assistenza o email privacy.",
    },
    "glovoapp.com": {
        "name": "Glovo",
        "domain": "glovoapp.com",
        "difficulty": DeletionDifficulty.MEDIUM,
        "delete_url": "https://glovoapp.com/it/faq",
        "dpo_email": "dpo@glovoapp.com",
        "notes": "Eliminazione richiedibile tramite app o contatto DPO.",
    },
    "booking.com": {
        "name": "Booking.com",
        "domain": "booking.com",
        "difficulty": DeletionDifficulty.EASY,
        "delete_url": "https://secure.booking.com/mytrips.html",
        "dpo_email": "dataprotectionoffice@booking.com",
        "notes": "Profilo utente > Sicurezza > Elimina account.",
    },
    "tripadvisor.com": {
        "name": "TripAdvisor",
        "domain": "tripadvisor.com",
        "difficulty": DeletionDifficulty.EASY,
        "delete_url": "https://www.tripadvisor.it/Settings-cp",
        "dpo_email": "privacy@tripadvisor.com",
        "notes": "Impostazioni account > Chiudi il tuo account.",
    },
}


def normalize_domain(domain_or_email: str) -> str:
    """Extract and normalize the root domain from a domain, host, or email."""
    if "@" in domain_or_email:
        domain_or_email = domain_or_email.split("@")[-1]
    
    domain_or_email = domain_or_email.lower().strip()
    
    # Strip protocols and paths if given a URL
    if "://" in domain_or_email:
        domain_or_email = domain_or_email.split("://")[1].split("/")[0]
    
    # Remove common subdomains
    parts = domain_or_email.split(".")
    if len(parts) > 2:
        # e.g., notifications.spotify.com -> spotify.com
        # handle special cases like amazon.co.uk or google.co.it
        if parts[-2] in ("co", "com", "org", "net", "gov") and len(parts) >= 3:
            return ".".join(parts[-3:])
        return ".".join(parts[-2:])
    return domain_or_email


def lookup_service(identifier: str) -> Optional[Dict[str, Any]]:
    """Lookup service details by domain, name, or email sender."""
    norm = normalize_domain(identifier)
    
    # Direct domain match
    if norm in SERVICES_DATABASE:
        return SERVICES_DATABASE[norm]
    
    # Name match
    clean_id = identifier.lower().replace(" ", "").replace("-", "")
    for domain, info in SERVICES_DATABASE.items():
        if info["name"].lower().replace(" ", "") == clean_id:
            return info
        if norm in domain or domain in norm:
            return info
            
    return None
