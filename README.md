# CleanSlate 🛡️

> **Local-First Digital Footprint Audit, One-Click Unsubscriber & GDPR Erasure Engine.**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![Tests](https://img.shields.io/badge/tests-13%2F13%20passed-brightgreen.svg)]()
[![Privacy](https://img.shields.io/badge/privacy-100%25%20local-success.svg)]()

CleanSlate è uno strumento progettato per trovare tutti gli account web registrati, gli abbonamenti ricorrenti e le mailing list associate a una casella di posta, offrendo strumenti immediati per disiscriversi e richiedere la cancellazione definitiva dei dati personali.

A differenza di servizi commerciali (come Unroll.me o Cleanfox) che archiviano o monetizzano i dati delle caselle postali, **CleanSlate viene eseguito al 100% in locale sulla tua macchina**. Nessun token o dato personale viene mai inviato al cloud.

---

## 🎯 Funzionalità Chiave

1. **OSINT Footprint Recon (Zero Password)**
   - Interroga in parallelo gli endpoint pubblici dei servizi web per rilevare account già registrati con quell'email, senza bisogno di accedere alla casella di posta.
2. **Local Inbox Audit (IMAP o MBOX offline)**
   - Connessione crittografata IMAP o parsing offline di archivi `.mbox` / `.eml` (es. Google Takeout, Thunderbird).
   - Analizza **esclusivamente gli header dei messaggi** (Subject, From, Date, List-Unsubscribe) per rilevare:
     - **Account registrati**: welcome email e conferme di registrazione.
     - **Abbonamenti e pagamenti**: ricevute, fatture e notifiche ricorrenti (Stripe, PayPal, ecc.).
     - **Newsletter e mailing list**: estrazione parametri RFC 2369 e RFC 8058.
3. **Action Hub: Disiscrizione e Cancellazione**
   - **RFC 8058 1-Click Unsubscribe**: disiscrizione istantanea tramite richiesta HTTP POST standardizzata (`List-Unsubscribe=One-Click`).
   - **Database JustDelete.me Integrato**: classificazione della difficoltà di cancellazione (*Facile, Media, Difficile, Impossibile*) e link diretto alla pagina di chiusura account.
   - **Generatore GDPR Articolo 17**: redazione automatica di richieste formali di diritto all'oblio in italiano e inglese, indirizzate al DPO aziendale con apertura immediata nel client di posta.

---

## 🏗️ Architettura del Progetto

```
cleanslate/
├── cleanslate/
│   ├── core/
│   │   ├── models.py         # Modelli dati Pydantic (ServiceEntry, ScanSummary)
│   │   ├── directory.py      # Database JustDelete.me e contatti DPO
│   │   ├── osint.py          # Probing asincrono endpoint web pubblici
│   │   ├── imap_scanner.py   # Motore di scansione IMAP e file MBOX/EML
│   │   └── actions.py        # Esecutore RFC 8058 e generatore Art. 17 GDPR
│   ├── web/
│   │   ├── app.py            # API REST FastAPI
│   │   └── static/           # Dashboard Web responsive (Dark Mode)
│   └── cli.py                # Interfaccia a riga di comando
├── tests/                    # Suite di test unitari (pytest)
├── requirements.txt
└── README.md
```

---

## 🚀 Avvio Rapido

### 1. Installazione

```bash
git clone https://github.com/pietromey/cleanslate.git
cd cleanslate

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Avvio Dashboard Web

```bash
python3 -m cleanslate.cli serve --port 8000
```
Apri il browser su `http://127.0.0.1:8000`. Puoi premere **"Carica Dati Demo"** per visualizzare all'istante uno scenario completo senza inserire credenziali.

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

La suite di test verifica la normalizzazione dei domini, il parsing degli header MIME, la categorizzazione euristica e gli endpoint API:

```bash
pytest -v
```

Risultato:
```
tests/test_actions.py::test_gdpr_generation_italian PASSED
tests/test_actions.py::test_gdpr_generation_english PASSED
tests/test_api.py::test_root_endpoint PASSED
tests/test_api.py::test_directory_search PASSED
tests/test_api.py::test_demo_data PASSED
tests/test_api.py::test_gdpr_template_api PASSED
tests/test_directory.py::test_normalize_domain PASSED
tests/test_directory.py::test_lookup_service PASSED
tests/test_parser.py::test_parse_sender PASSED
tests/test_parser.py::test_parse_unsubscribe_header PASSED
tests/test_parser.py::test_classify_welcome_email PASSED
tests/test_parser.py::test_classify_billing_email PASSED
tests/test_parser.py::test_classify_newsletter_email PASSED
13 passed in 0.56s
```

---

## ⚖️ Note sulla Privacy

CleanSlate non richiede la password principale del tuo account Google o Microsoft: supporta le normali **Password per le app** e l'importazione manuale di file `.mbox` esportati con Google Takeout. Tutti i controlli risiedono nella RAM del processo locale e nessun dato viene inviato a server terzi.
