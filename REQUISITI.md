# Requisiti di CleanSlate

## Cosa si installa oggi

Il pacchetto di prova `dist/CleanSlate-1.0.0-macos-arm64.zip` include **Python e dipendenze**: la sua `CleanSlate.app` al primo livello si può copiare in Applicazioni. Richiede Apple Silicon e macOS 26+; è verificato su macOS 26.3. Firma locale ad-hoc, nessuna notarizzazione Apple, pubblicazione ancora da fare. La [guida del pacchetto](docs/INSTALLAZIONE_MACOS.md) spiega installazione, demo, limiti e ricostruzione.

Per lavorare sui **sorgenti**, invece, si installano le dipendenze Python nella stessa cartella. La `CleanSlate.app` nella radice del repository rimane un launcher: non contiene Python né le librerie e non va copiata da sola in Applicazioni. Le istruzioni qui sotto si riferiscono a questa installazione dai sorgenti.

Non servono Officina, Homebrew, Node.js per usare l'app, account dello sviluppatore o chiavi API a pagamento. L'installazione iniziale richiede Internet per scaricare le librerie da PyPI. Non copiare `venv` fra computer: va ricreato con il Python della macchina di destinazione.

## Piattaforme e strumenti

| Uso | Requisiti e limiti |
| --- | --- |
| Dashboard nel browser e CLI | Python **3.10 o successivo**, `venv` e `pip`; browser moderno con JavaScript e localStorage. Nessun compilatore frontend o servizio web esterno. |
| Finestra desktop macOS | pywebview e i bridge PyObjC installati da pip, Cocoa/WebKit del sistema. Il launcher dichiara macOS 11 come minimo, ma questo non certifica ogni combinazione di macOS, architettura e Python: anche le librerie devono avere versioni compatibili. |
| Password salvate | Solo Portachiavi macOS; negli altri sistemi inserire la password a ogni scansione. |
| Windows/Linux | Codice web/CLI progettato senza percorsi macOS obbligatori, ma **non collaudato su queste piattaforme**. Per il desktop servono inoltre i componenti indicati nella [guida pywebview](https://pywebview.flowrl.com/guide/installation), come WebView2 su Windows o un backend Qt/GTK su Linux. |
| Test Python | pytest, già incluso nel file dei requisiti. Non richiedono credenziali o scansioni reali. |
| Test dell'interfaccia | Node.js con `node:test` (18 o successivo); nessun pacchetto npm. |

Il controllo di portabilità del 1° ottobre 2026 usa macOS Darwin 25.3.0, Apple Silicon arm64 e Python 3.14.7. Le altre versioni di Python e i Mac Intel non sono stati collaudati in questa sessione.

## Installazione dai sorgenti

Aprire un terminale **nella cartella che contiene `requirements.txt`**. Non è necessario un percorso particolare; sono ammessi spazi nel nome.

macOS/Linux:

```bash
python3 --version
python3 -m venv venv
venv/bin/python -m pip install -r requirements.txt
venv/bin/python -m pip check
venv/bin/python -m cleanslate.cli serve --port 8000
```

Aprire `http://127.0.0.1:8000` e scegliere **Carica Dati Demo**. Per fermare il server premere Ctrl+C. Se la porta è occupata usare, per esempio, `--port 8001` e aprire quell'indirizzo.

Su macOS, dopo l'installazione, si può aprire `CleanSlate.app` dalla cartella dei sorgenti oppure eseguire:

```bash
venv/bin/python -m cleanslate.desktop
```

Per Windows (PowerShell), la sequenza equivalente per la dashboard è:

```powershell
py -3 -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe -m pip check
.\venv\Scripts\python.exe -m cleanslate.cli serve --port 8000
```

I comandi Windows sono istruzioni da verificare su quella piattaforma. Non esiste ancora un installer Windows. Il bundle macOS non si usa su Windows/Linux.

## Dipendenze dichiarate

`requirements.txt` è l'unico elenco da installare. pip risolve anche le dipendenze indirette; non bisogna aggiungerle a mano dal computer dello sviluppatore.

| Pacchetto | Funzione |
| --- | --- |
| fastapi, uvicorn | API e server locale |
| httpx | Richieste HTTP OSINT e disiscrizione; client dei test |
| pydantic | Modelli e validazione |
| python-multipart | Caricamento file MBOX/EML |
| pywebview | Finestra desktop |
| pyobjc-framework-Cocoa (solo macOS) | Bridge Foundation usato per il nome CleanSlate nella GUI; gli altri bridge desktop sono richiesti da pywebview |
| holehe | Moduli OSINT e relative dipendenze (tra cui trio e BeautifulSoup) |
| keyring | Accesso al Portachiavi macOS |
| certifi | Certificati radice inclusi per verificare identità e certificato del server IMAP anche senza Python/Homebrew installati |
| pytest | Test di sviluppo |

Le versioni minime sono in `requirements.txt`; il file non blocca tutte le versioni a quelle provate. Non è quindi un lock per build identiche. Licenze e versioni dell'inventario sono in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). Il pacchetto generato contiene anche versioni risolte, sorgenti delle dipendenze, licenze e inventario dei moduli effettivamente inclusi.

## Configurazione e percorsi

| Impostazione | Comportamento |
| --- | --- |
| `CLEANSLATE_PYTHON` | Solo launcher `.app`: percorso **assoluto** di un interprete Python eseguibile con i requisiti installati; predefinito `venv/bin/python3` relativo alla cartella del progetto. Non accetta argomenti aggiuntivi. |
| `CLEANSLATE_PORT` | Solo desktop: intero da 1 a 65535. Senza valore usa 47863, poi le nove porte successive se occupata. Se esplicita e occupata interrompe l'avvio. |
| `serve --host` / `--port` | Solo dashboard CLI; predefiniti `127.0.0.1` e 8000. Lasciare il bind locale: il server non prevede autenticazione per l'accesso da altri computer. |
| Server IMAP e porta | Si inseriscono nell'interfaccia, oppure si scelgono i preset modificabili o un profilo salvato. La porta usuale è 993 con TLS. Nessuna scoperta automatica in rete. |
| File di interfaccia | Cercati rispetto al modulo `cleanslate/web/app.py`, indipendentemente dalla directory corrente; API e asset usano URL relativi all'origine corrente. Nessun CDN. |
| `~/.cleanslate/profiles.json` | Metadati dei profili dell'utente corrente, senza password. |
| `~/.cleanslate/webview` | Dati persistenti del browser desktop. L'ultimo profilo è in localStorage; nessuna password. |

Esempio di avvio configurato dal terminale nella cartella dei sorgenti:

```bash
CLEANSLATE_PYTHON="$PWD/venv/bin/python3" CLEANSLATE_PORT=47870 \
  ./CleanSlate.app/Contents/MacOS/CleanSlate
```

Le variabili impostate nel terminale valgono per quel comando; il doppio clic dal Finder non legge automaticamente la configurazione della shell. CleanSlate non legge file `.env`. Le password non vanno messe in variabili, comandi o file di configurazione: si inseriscono nell'interfaccia e, se desiderato, nel Portachiavi.

## Rete e dati

Demo, directory locale, generazione del testo GDPR e analisi MBOX/EML possono funzionare offline. Le scansioni OSINT contattano i servizi pubblici via HTTPS; IMAP contatta il server di posta indicato con TLS; la disiscrizione contatta l'indirizzo fornito dal mittente. I link esterni si aprono su richiesta dell'utente. Non servono porte in ingresso sul router né un servizio di scoperta in LAN.

Per IMAP servono un account abilitato all'accesso IMAP e credenziali accettate dal provider (eventualmente una password per app). CleanSlate usa login IMAP con password, non implementa OAuth: un preset non garantisce che la politica attuale del provider o dell'organizzazione consenta l'accesso. Errori e limiti dei servizi OSINT non significano assenza di account: vedere [l'indagine OSINT](docs/osint-servizi.md).

I dati della scansione restano nella memoria dell'app; profili e selezione persistono come indicato sopra. Spostare i sorgenti non trasferisce il Portachiavi su un altro Mac e non richiede di eliminare i profili del Mac attuale. La nuova installazione va configurata nell'interfaccia.

## Profili IMAP e Portachiavi macOS

- Il salvataggio delle password richiede macOS, un Portachiavi disponibile e `keyring>=25.6,<26`, dichiarato in `requirements.txt`. CleanSlate usa direttamente il backend macOS di keyring, senza passare password agli argomenti di processi e senza archivi alternativi. Le operazioni sul Portachiavi possono richiedere l'autorizzazione di macOS.
- Per macOS 11 e successivi consultare i requisiti dell'interprete nella [documentazione di keyring](https://keyring.readthedocs.io/en/latest/#compatibility-macos). L'ambiente verificato per i test automatici di questa funzione usa Python 3.14 e keyring 25.7.0. Questi test simulano il Portachiavi: non sostituiscono la prova nell'app reale.
- I profili contengono solo nome, server, porta e utente, nel file `~/.cleanslate/profiles.json`. L'identificativo dei nuovi profili è `utente@server:porta` in minuscolo; lo stesso identificativo è l'account della voce `com.cleanslate.imap` in Accesso Portachiavi. Le password restano nel Portachiavi e nella memoria necessaria alla connessione; non sono restituite nelle risposte API o nei messaggi di errore.
- I profili creati dalla versione preliminare con un nome breve restano utilizzabili ed eliminabili con quel nome. Salvarli di nuovo crea un identificativo completo; l'eventuale vecchio profilo si elimina dall'interfaccia. Non viene eseguita una migrazione automatica delle password.
- L'ultimo profilo selezionato è ricordato in `localStorage`, alla chiave `cleanslate.lastImapProfile`: contiene solo l'identificativo. L'app desktop usa un'origine stabile su `127.0.0.1:47863` e la persistenza web di pywebview. Se quella porta è occupata usa la prima libera delle nove successive (in quel caso l'ultimo profilo va riselezionato); se sono tutte occupate l'avvio si interrompe con un avviso. Si può fissare un'altra porta con `CLEANSLATE_PORT`, mantenendola uguale nei successivi avvii. Cambiare porta o cancellare i dati web richiede di selezionare nuovamente il profilo. Con un solo profilo la selezione è automatica.
- Negli altri sistemi operativi il salvataggio nel Portachiavi macOS non è disponibile: rimane possibile inserire la password per ogni scansione. I test automatici non usano credenziali reali; quelli dell'interfaccia richiedono Node.js con `node:test`.

### Prova nell'app dopo la revisione della fase A

1. Aprire CleanSlate.app, compilare i dati IMAP e scegliere **Salva profilo**; autorizzare l'accesso al Portachiavi se macOS lo richiede.
2. Chiudere e riaprire l'app: verificare che il profilo sia selezionato, con server, porta e utente compilati e il campo password vuoto.
3. Avviare una scansione senza inserire la password e verificare che termini con i risultati.
4. Selezionare **Elimina**, confermare e verificare in Accesso Portachiavi che la voce del servizio `com.cleanslate.imap` con l'identificativo di quel profilo sia scomparsa.

## Esito del controllo di portabilità (1° ottobre 2026)

Installazione da PyPI in un venv vuoto e copia dei sorgenti in un percorso con spazi: dipendenze coerenti (`pip check`), import riusciti, **112 test Python passati**, API/demo/risorse statiche e CLI funzionanti. Dopo un'interruzione della sessione, gli ultimi passi sono stati ripresi nella stessa copia senza reinstallare. Il controllo usa FastAPI 0.142.2, pywebview 6.2.1, PyObjC Cocoa 12.2.2 e keyring 25.7.0; nessuna credenziale reale. Rimane un avviso di deprecazione Starlette/httpx nei test. Nell'ambiente di lavoro passano anche i **9 test Node**, eseguiti con Node.js 26.9.0.

## Verifiche ripetibili

Dalla cartella dei sorgenti:

```bash
venv/bin/python -m pytest -q
node --test tests/test_imap_ui.cjs tests/test_osint_ui.cjs
venv/bin/python -m pip check
venv/bin/python scripts/check_portability.py
```

L'ultimo comando richiede rete per pip e spazio per un secondo ambiente Python temporaneo. Copia solo sorgenti, launcher, requisiti e test in un percorso con spazi, crea un venv vuoto, installa i requisiti e verifica import, suite Python, risorse statiche, demo e CLI. Elimina la copia al termine; non apre finestre, non esegue scansioni e non legge password. I test del launcher controllano anche avvio da una directory estranea, interprete configurato e interprete mancante.

La prova automatica del nome macOS controlla i valori Cocoa in un processo separato. La visualizzazione effettiva della barra menu richiede ancora una prova manuale aprendo CleanSlate.app. Le prove manuali IMAP e di persistenza dei profili erano già state confermate da Pietro prima di questo lavoro.
