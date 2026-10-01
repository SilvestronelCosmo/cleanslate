"""CleanSlate Command Line Interface."""

import argparse
import asyncio
import sys
from cleanslate.core.models import GDPRRequestPayload
from cleanslate.core.directory import SERVICES_DATABASE, lookup_service
from cleanslate.core.osint import run_osint_scan
from cleanslate.core.actions import generate_gdpr_deletion_request


def print_banner():
    banner = r"""
   ________                  _____ __      __     
  / ____/ /__  ____ _____   / ___// /___ _/ /____ 
 / /   / / _ \/ __ `/ __ \  \__ \/ / __ `/ __/ _ \
/ /___/ /  __/ /_/ / / / / ___/ / / /_/ / /_/  __/
\____/_/\___/\__,_/_/ /_/ /____/_/\__,_/\__/\___/ 
      Local-First Digital Footprint Audit
"""
    print(banner)


async def cmd_scan(email: str):
    print(f"[*] Avvio scansione OSINT per: {email}")
    print("[*] Interrogazione endpoint pubblici in corso...")
    
    results, unverified = await run_osint_scan(email)
    
    print("\n" + "=" * 70)
    print(f"  RISULTATI AUDIT PER: {email}")
    print("=" * 70)

    if unverified:
        details = ", ".join(f"{item['domain']} ({item['cause']})" for item in unverified)
        print(f"[!] Non verificabili: {details}")
    
    if not results:
        print("[!] Nessun account pubblico o registrazione rilevata.")
        return
        
    for idx, s in enumerate(results, 1):
        print(f"\n[{idx}] {s.name} ({s.domain})")
        print(f"    Categoria:     {s.category.value.upper()}")
        print(f"    Difficoltà:    {s.difficulty.value.upper()}")
        if s.delete_url:
            print(f"    Link Canc.:    {s.delete_url}")
        if s.dpo_email:
            print(f"    Email DPO:     {s.dpo_email}")
        if s.notes:
            print(f"    Note:          {s.notes}")
            
    print("\n" + "=" * 70)
    print(f"Totale account identificati: {len(results)}")
    print("=" * 70)


def cmd_gdpr(service: str, name: str, email: str, lang: str = "it"):
    info = lookup_service(service) or {}
    dpo = info.get("dpo_email")
    payload = GDPRRequestPayload(
        user_name=name,
        user_email=email,
        service_name=info.get("name", service),
        dpo_email=dpo,
        language=lang,
    )
    result = generate_gdpr_deletion_request(payload)
    print("\n" + "=" * 70)
    print("  LETTERA ESERCIZIO DIRITTO ALL'OBLIO (ART. 17 GDPR)")
    print("=" * 70)
    print(f"Destinatario: {result['dpo_email']}")
    print(f"Oggetto:      {result['subject']}\n")
    print(result["body"])
    print("=" * 70)


def cmd_directory(query: str = ""):
    print("\n" + "=" * 70)
    print("  DATABASE JUSTDELETE.ME & CONTATTI DPO")
    print("=" * 70)
    q = query.lower().strip()
    matches = [
        item for item in SERVICES_DATABASE.values()
        if not q or q in item["name"].lower() or q in item["domain"].lower()
    ]
    for s in matches:
        print(f"• {s['name']:<18} [{s['difficulty'].value.upper():<10}] {s.get('delete_url', 'N/D')}")
    print(f"\nTotale visualizzati: {len(matches)}")


def cmd_serve(host: str = "127.0.0.1", port: int = 8000):
    import uvicorn
    print(f"[*] Avvio dashboard CleanSlate su http://{host}:{port}")
    uvicorn.run("cleanslate.web.app:app", host=host, port=port, reload=False)


def main():
    print_banner()
    parser = argparse.ArgumentParser(description="CleanSlate - Local Digital Footprint Audit & Unsubscriber")
    subparsers = parser.add_subparsers(dest="command")

    # scan
    p_scan = subparsers.add_parser("scan", help="Esegui scansione OSINT su indirizzo email")
    p_scan.add_argument("email", help="Indirizzo email da analizzare")

    # gdpr
    p_gdpr = subparsers.add_parser("gdpr", help="Genera richiesta cancellazione Art. 17 GDPR")
    p_gdpr.add_argument("--service", required=True, help="Nome servizio (es. Spotify, Netflix)")
    p_gdpr.add_argument("--name", required=True, help="Tuo nome e cognome")
    p_gdpr.add_argument("--email", required=True, help="Tua email registrata")
    p_gdpr.add_argument("--lang", default="it", choices=["it", "en"], help="Lingua (it o en)")

    # directory
    p_dir = subparsers.add_parser("directory", help="Cerca nel database di cancellazione servizi")
    p_dir.add_argument("query", nargs="?", default="", help="Filtro per nome o dominio")

    # serve
    p_serve = subparsers.add_parser("serve", help="Avvia il server web dashboard")
    p_serve.add_argument("--host", default="127.0.0.1", help="Host IP")
    p_serve.add_argument("--port", type=int, default=8000, help="Porta HTTP")

    args = parser.parse_args()

    if args.command == "scan":
        asyncio.run(cmd_scan(args.email))
    elif args.command == "gdpr":
        cmd_gdpr(args.service, args.name, args.email, args.lang)
    elif args.command == "directory":
        cmd_directory(args.query)
    elif args.command == "serve":
        cmd_serve(args.host, args.port)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
