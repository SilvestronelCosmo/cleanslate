# CleanSlate 1.0.0 per Mac — pacchetto di prova


Questo pacchetto contiene una **vera app autonoma**: Python e le librerie sono inclusi. Non occorrono Terminale, Python, Homebrew o Officina per usarla. È una build da revisionare, non ancora pubblicata né notarizzata da Apple.

## Installazione e demo

1. Espandi `CleanSlate-1.0.0-macos-arm64.zip` con un doppio clic.
2. Trascina la `CleanSlate.app` che trovi nella cartella estratta in **Applicazioni** (oppure in una cartella a tua scelta).
3. Apri l'app. Premi **Dati Demo**: compaiono servizi di esempio senza account, password o chiamate a servizi esterni.
4. Chiudi CleanSlate dal menu o chiudendo la finestra.

La `.app` nella cartella `sorgenti` è invece l'avviatore per chi sviluppa: per la prova usa quella al primo livello dell'archivio.

## Mac compatibili e primo avvio

- **Apple Silicon (M1 o successivo), macOS 26 o successivo**. La build è verificata su macOS 26.3 arm64; le altre versioni non sono collaudate. I Mac Intel non sono supportati da questo archivio.
- Firma locale **ad-hoc**, senza identità Developer ID e senza notarizzazione. Dopo un download macOS può bloccare il primo avvio. Solo se conosci e ti fidi della provenienza, segui l'opzione **Apri comunque** in Impostazioni di Sistema → Privacy e Sicurezza. Non occorre disattivare Gatekeeper o rimuovere protezioni dal Terminale. Se l'opzione non è disponibile, attendi un pacchetto firmato.
- Questo limite riguarda la distribuzione. La firma ad-hoc controllata nei test non certifica l'identità dell'autore.

Guida Apple: <https://support.apple.com/it-it/102445>.

## Dati e funzioni

La demo funziona offline. OSINT richiede Internet e invia l'indirizzo ai servizi interrogati; IMAP usa una connessione diretta al provider. I servizi OSINT non verificabili restano esplicitamente tali: il pacchetto non cambia i limiti dei provider.

I profili restano in `~/.cleanslate/profiles.json`; le password salvate restano nel Portachiavi macOS. Al primo accesso dalla nuova app macOS può chiedere un'autorizzazione. Non includere password in segnalazioni di problemi. La demo e le verifiche automatiche non leggono il Portachiavi.

**Limite IMAP.** IMAP verifica sempre il certificato e il nome del server. I server con certificato autofirmato (per esempio i bridge locali) non sono supportati: la connessione viene rifiutata e il controllo non si può disattivare.

Per disinstallare, chiudi l'app e spostala nel Cestino. Profili e password non vengono cancellati: elimina prima i profili dall'interfaccia se vuoi rimuoverli. Non è necessario cancellare dati per reinstallare.

## Contenuto e riproduzione per il revisore

- `CleanSlate.app`: app autonoma e testi di licenza in `Contents/Resources/legal`.
- `sorgenti`: codice CleanSlate, test, ricetta di build e `packaging/requirements-resolved.txt` con versioni esatte dell'ambiente usato.
- `sorgenti-dipendenze`: archivi originali PyPI delle dipendenze e strumenti di build, incluse quelle indirette. I relativi hash e URL sono in `CleanSlate.app/Contents/Resources/legal/python-environment.json`. Questo inventario comprende l'intero ambiente, anche gli strumenti non incorporati nell'app; i moduli effettivamente inclusi sono in `BUILD-INFO.json`.
- `BUILD-INFO.json`: piattaforma, moduli, librerie native e hash dei sorgenti CleanSlate della build.
- `LICENSE`: licenza GPL-3.0-only di CleanSlate. Le dipendenze mantengono le rispettive licenze.

Il file `.sha256` consegnato accanto allo ZIP permette di controllarne l'integrità. Non è una firma dell'autore.

Ricostruzione su Mac arm64 con Python 3.14 e strumenti da riga di comando Apple, dalla cartella `sorgenti` (oppure dal repository):

```bash
python3 -m venv build/venv-macos
build/venv-macos/bin/python -m pip install -r packaging/requirements-build.txt
# Per le stesse versioni, se presente nell'archivio:
build/venv-macos/bin/python -m pip install -r packaging/requirements-resolved.txt
build/venv-macos/bin/python scripts/build_macos.py
build/venv-macos/bin/python scripts/check_macos_package.py
build/venv-macos/bin/python scripts/check_macos_package.py --gui
```

La prima build scarica gli archivi dei sorgenti da PyPI e ne verifica gli hash. Li conserva in `build/dependency-sources` per le build successive. Lo script inventaria anche le librerie native del Python Homebrew usato: una provenienza o licenza non riconosciuta interrompe la build e richiede di estendere l'inventario. Per ricostruire su un altro Python o macOS serve una nuova verifica; non viene promessa identità binaria fra computer.

Il controllo `--gui` richiede una sessione grafica macOS: apre brevemente una finestra, carica la demo e la chiude. Tutti i controlli usano una cartella utente temporanea e non leggono password o profili reali. La prova manuale di IMAP/Portachiavi sul nuovo bundle e il comportamento Gatekeeper dopo un download restano distinti da questi controlli.

Esito della prova locale del 1° ottobre 2026: app estratta fuori dal progetto, runtime Python incluso, 13 moduli Holehe importabili, risorse e API funzionanti, demo di otto servizi caricata anche nella vera finestra WebKit. Verificati 71 binari Mach-O senza dipendenze assolute da Homebrew; 114 test Python e 9 test dell'interfaccia passano. L'avvio del runtime Cocoa richiede accesso alla sessione macOS: in un sandbox che lo impedisce il processo può essere interrotto anche nella verifica senza `--gui`.

Ricetta basata sulla [documentazione PyInstaller](https://pyinstaller.org/en/stable/feature-notes.html#macos-multi-arch-support) e sulle [indicazioni di packaging pywebview](https://pywebview.flowrl.com/guide/freezing.html).
