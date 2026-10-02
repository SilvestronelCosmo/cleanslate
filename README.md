# CleanSlate 🛡️

> **Local-First Digital Footprint Audit, One-Click Unsubscriber & GDPR Erasure Engine.**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)

CleanSlate è uno strumento progettato per trovare account web registrati, abbonamenti ricorrenti e mailing list associate a una casella di posta, offrendo strumenti immediati per disiscriversi e richiedere la cancellazione definitiva dei dati personali.

A differenza di servizi commerciali (come Unroll.me o Cleanfox) che archiviano o monetizzano i dati delle caselle postali, CleanSlate viene eseguito in locale sulla tua macchina senza inviare token o credenziali di posta al cloud.

---

## 🔒 Cosa esce dalla tua macchina

La trasparenza sui dati di rete inviati è totale:

| Modalità | Cosa esce |
|---|---|
| **OSINT** | L'indirizzo email viene inviato a 16 servizi (a Gravatar il suo hash MD5) |
| **IMAP** | Connessione diretta esclusivamente verso il tuo provider di posta |
| **MBOX** | Nulla (elaborazione al 100% offline in locale) |
| **Unsubscribe** | Una richiesta HTTP POST/GET all'indirizzo di disiscrizione fornito dal mittente |
| **GDPR** | Nulla (genera il testo e predispone l'URI `mailto:` per il tuo client di posta locale) |
| **Demo** | Nulla (nessuna richiesta di rete) |

---

## 🎯 Funzionalità Chiave

1. **OSINT Footprint Recon (Zero Password)**
   - Interroga in parallelo gli endpoint di 16 piattaforme (Twitter/X, Spotify, Duolingo, GitHub, Gravatar, Discord, Deliveroo, Patreon, SoundCloud, Last.fm, Snapchat, Strava, Docker Hub, Tumblr, Proton Mail) per rilevare registrazioni pubbliche, senza richiedere password o accesso alla casella di posta.
2. **Local Inbox Audit (IMAP o MBOX offline)**
   - Connessione crittografata IMAP o parsing offline di archivi `.mbox` / `.eml` (es. Google Takeout, Thunderbird).
   - Analizza **esclusivamente gli header dei messaggi** (Subject, From, Date, List-Unsubscribe) per rilevare:
     - **Account registrati**: welcome email e conferme di registrazione.
     - **Abbonamenti e pagamenti**: ricevute, fatture e notifiche ricorrenti (Stripe, PayPal, ecc.).
     - **Newsletter e mailing list**: estrazione parametri RFC 2369 e RFC 8058.
3. **Action Hub: Disiscrizione e Cancellazione**
   - **RFC 8058 1-Click Unsubscribe**: disiscrizione istantanea tramite richiesta HTTP POST standardizzata (`List-Unsubscribe=One-Click`).
   - **Selezione locale ispirata a JustDelete.me**: classificazione della difficoltà di cancellazione (*Facile, Media, Difficile, Impossibile*) e link diretto alla pagina di chiusura account.
   - **Generatore GDPR Articolo 17**: redazione automatica di richieste formali di diritto all'oblio in italiano e inglese, indirizzate al DPO aziendale con apertura immediata nel client di posta.

---

## 🍏 App macOS

Il pacchetto di prova `dist/CleanSlate-1.0.0-macos-arm64.zip` contiene un'app autonoma per **Mac Apple Silicon con macOS 26+**: include Python e librerie, si estrae e si copia in Applicazioni. È una build locale da revisionare, con firma ad-hoc e senza notarizzazione Apple; non è ancora un download pubblico. Vedi [installazione e prova demo](docs/INSTALLAZIONE_MACOS.md).

La `CleanSlate.app` nella radice dei **sorgenti** resta invece il launcher di sviluppo e richiede il venv accanto. Dopo aver installato i requisiti:
```bash
open CleanSlate.app
```
oppure direttamente con Python:
```bash
venv/bin/python cleanslate/desktop.py
```
L'app usa una porta locale a partire da 47863. La demo funziona offline; OSINT e IMAP richiedono rete.

---

## ⚠️ Limiti noti

- **Holehe non mantenuto**: i moduli per la verifica OSINT derivano dalla libreria Holehe (sotto licenza GPL-3.0), che non è attivamente manutenuta. Eventuali modifiche agli endpoint dei servizi esterni possono causare falsi negativi o rate limit, che vengono segnalati dall'applicazione tra i servizi "non verificabili".
- **Accesso IMAP Outlook**: Microsoft ha progressivamente rimosso l'accesso IMAP tramite password semplici per gli account personali gratuiti.
- **Tetti alle email scansionate**: il parser MBOX analizza fino a 500 messaggi per archivio; la scansione IMAP accetta un intervallo da 1 a 1000 email (default 150) per preservare reattività e memoria.

---

## 🏗️ Architettura del Progetto

```
cleanslate/
├── CleanSlate.app/           # Bundle applicazione nativa macOS (pywebview)
├── cleanslate/
│   ├── core/
│   │   ├── models.py         # Modelli dati Pydantic (ServiceEntry, ScanSummary)
│   │   ├── directory.py      # Selezione locale di percorsi di cancellazione e contatti DPO
│   │   ├── osint.py          # Probing asincrono (16 servizi, moduli Holehe)
│   │   ├── imap_scanner.py   # Motore di scansione IMAP e file MBOX/EML
│   │   └── actions.py        # Esecutore RFC 8058 e generatore Art. 17 GDPR
│   ├── web/
│   │   ├── app.py            # API REST FastAPI (zero CORS aperto)
│   │   └── static/           # Dashboard Web responsive (senza dipendenze remote)
│   ├── desktop.py            # Launcher desktop nativo su porta dinamica
│   └── cli.py                # Interfaccia a riga di comando
├── tests/                    # Suite di test unitari offline (pytest)
│   ├── test_actions.py
│   ├── test_api.py
│   ├── test_directory.py
│   ├── test_osint.py
│   └── test_parser.py
├── requirements.txt
└── README.md
```

---

## 🚀 Avvio Rapido

### 1. Installazione

Dalla cartella dei sorgenti, con Python 3.10 o successivo. Vedi [REQUISITI.md](REQUISITI.md) per piattaforme, configurazione, rete e limiti verificati.

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Avvio Dashboard Web

```bash
python3 -m cleanslate.cli serve --port 8000
```
Su macOS, dopo l'installazione, puoi anche aprire `CleanSlate.app` dalla cartella dei sorgenti oppure eseguire `python3 -m cleanslate.desktop`. Questo launcher richiede i sorgenti e `venv` accanto a sé. Dopo aver copiato i sorgenti su un altro computer, ricrea `venv`. Il pacchetto autonomo descritto sopra non richiede questi passaggi.

Apri il browser su `http://127.0.0.1:8000`. Puoi premere **"Carica Dati Demo"** per visualizzare all'istante uno scenario completo senza inserire credenziali e senza effettuare chiamate di rete.

### 3. Utilizzo via CLI

**Scansione OSINT rapida su un indirizzo email:**
```bash
python3 -m cleanslate.cli scan utente@esempio.com
```

**Generazione richiesta di cancellazione GDPR Art. 17:**
```bash
python3 -m cleanslate.cli gdpr --service Spotify --name "Mario Rossi" --email "mario@esempio.com" --lang it
```

**Ricerca nel database di cancellazione:**
```bash
python3 -m cleanslate.cli directory netflix
```

---

## 🧪 Esecuzione dei Test

La suite di test verifica la normalizzazione dei domini, la prevenzione da path traversal, l'assenza di header CORS non necessari, il parsing degli header MIME, la categorizzazione euristica e il probing OSINT con mock offline:

```bash
venv/bin/python -m pytest -v
```

Risultato reale:
```
tests/test_actions.py::test_gdpr_generation_italian PASSED               [  4%]
tests/test_actions.py::test_gdpr_generation_english PASSED               [  9%]
tests/test_api.py::test_root_endpoint PASSED                             [ 14%]
tests/test_api.py::test_directory_search PASSED                          [ 19%]
tests/test_api.py::test_demo_data PASSED                                 [ 23%]
tests/test_api.py::test_gdpr_template_api PASSED                         [ 28%]
tests/test_api.py::test_no_cors_header PASSED                            [ 33%]
tests/test_api.py::test_mbox_upload_filename_traversal PASSED            [ 38%]
tests/test_api.py::test_osint_endpoint_reports_unverified PASSED         [ 42%]
tests/test_api.py::test_unsubscribe_rejects_non_http PASSED              [ 47%]
tests/test_directory.py::test_normalize_domain PASSED                    [ 52%]
tests/test_directory.py::test_lookup_service PASSED                      [ 57%]
tests/test_directory.py::test_lookup_no_substring_false_positive PASSED  [ 61%]
tests/test_osint.py::test_holehe_modules_importable PASSED               [ 66%]
tests/test_osint.py::test_osint_service_names_count PASSED               [ 71%]
tests/test_osint.py::test_run_osint_scan_maps_and_dedupes PASSED         [ 76%]
tests/test_parser.py::test_parse_sender PASSED                           [ 80%]
tests/test_parser.py::test_parse_unsubscribe_header PASSED               [ 85%]
tests/test_parser.py::test_classify_welcome_email PASSED                 [ 90%]
tests/test_parser.py::test_classify_billing_email PASSED                 [ 95%]
tests/test_parser.py::test_classify_newsletter_email PASSED              [100%]
======================== 21 passed in 0.37s =========================
```

---

## 📜 Crediti e Licenze terze

CleanSlate è distribuito sotto [GNU GPL versione 3 soltanto](LICENSE) (`GPL-3.0-only`). Il codice di Holehe usato per le verifiche OSINT conserva la propria licenza GPL-3.0; JustDelete.me è un riferimento per la selezione locale di percorsi di cancellazione. Le licenze delle dipendenze dirette, le fonti e le condizioni per un futuro pacchetto scaricabile sono in [Crediti e licenze di terzi](THIRD_PARTY_NOTICES.md).
