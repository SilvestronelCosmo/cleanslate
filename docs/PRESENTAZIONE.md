# CleanSlate — materiali per la presentazione

Materiali per la pagina su pietromey.com. La pagina e la pubblicazione si fanno nel progetto pietromey; qui ci sono testi e catture pronti da usare. Le catture sono in `.officina/galleria/sito/` (con accanto il file `.json` di provenienza), fatte con i Dati Demo e senza dati reali.

## Testo di presentazione

**CleanSlate — ritrova i tuoi account dimenticati, disiscriviti, chiedi la cancellazione dei dati.**

CleanSlate è un'app per Mac che cerca gli account registrati, gli abbonamenti e le newsletter legati al tuo indirizzo email. Per ogni servizio trovato ti mostra quanto è difficile chiudere l'account, ti porta alla pagina giusta e, dove il mittente lo permette, ti disiscrive con un clic. Se vuoi cancellare i tuoi dati, prepara una richiesta formale di cancellazione (Art. 17 GDPR, in italiano o inglese) pronta da aprire nel tuo programma di posta.

È pensata per chi vuole fare pulizia nella propria presenza online senza consegnare la posta a un servizio esterno: tutto gira sul tuo Mac, senza account e senza cloud di CleanSlate. È software libero (GPL-3.0).

## Cosa resta sul Mac e cosa esce

| Modalità | Cosa esce dal Mac |
|---|---|
| Dati Demo | Nulla (nessuna richiesta di rete) |
| Archivio MBOX / EML | Nulla (elaborazione offline) |
| IMAP | Solo la connessione diretta al tuo provider di posta; vengono lette soltanto le intestazioni dei messaggi |
| OSINT | **L'indirizzo email viene inviato a 16 servizi** (a Gravatar ne va l'impronta MD5) per verificare se esiste una registrazione |
| Disiscrizione | Una richiesta all'indirizzo di disiscrizione indicato dal mittente |
| Richiesta GDPR | Nulla: il testo si copia o si apre nel tuo client di posta |

Le password IMAP salvate stanno nel Portachiavi di macOS; i profili (server e utente, senza password) in `~/.cleanslate/profiles.json`. Nessuna chiave API, nessun account CleanSlate.

## Funzioni principali

- **Scansione OSINT, senza password**: verifica in parallelo la registrazione su 16 servizi (tra cui GitHub, Spotify, Discord, Deliveroo, Strava, Tumblr). I servizi che non rispondono in modo affidabile sono elencati a parte come «non verificabili», con la causa osservata: non vanno letti come «account assente».
- **Controllo della casella via IMAP**: analizza solo le intestazioni (oggetto, mittente, data, `List-Unsubscribe`) per riconoscere account, ricevute e abbonamenti, newsletter. Profili salvati nel Portachiavi, tempo trascorso e durata finale mostrati durante la scansione (fino a 1000 messaggi per scansione).
- **Archivi offline MBOX / EML**: per esempio da Google Takeout o Thunderbird (fino a 500 messaggi per archivio).
- **Disiscrizione con un clic** (RFC 8058) dove il mittente la supporta.
- **Difficoltà di cancellazione** (facile, media, difficile) e link alla pagina di chiusura account, con una selezione locale ispirata a JustDelete.me.
- **Generatore di richieste GDPR Art. 17** in italiano e inglese, indirizzate al responsabile privacy del servizio.
- **Dati Demo**: otto servizi di esempio per provare l'interfaccia, offline.

## Requisiti

- Mac con **Apple Silicon (M1 o successivo)** e **macOS 26 o successivo** (verificato su macOS 26.3). I Mac Intel non sono supportati dal pacchetto.
- Python e librerie sono già inclusi nell'app: non servono Terminale, Python o Homebrew.
- OSINT e IMAP richiedono Internet; la demo e gli archivi MBOX funzionano offline.
- IMAP verifica sempre il certificato del server: i server con certificato autofirmato non sono supportati. Alcuni provider (per esempio Outlook personale) non accettano più l'accesso IMAP con password semplice.

## Avviso del primo avvio

L'app è firmata solo in locale (firma ad-hoc) e **non è notarizzata da Apple**. Dopo il download macOS può bloccare il primo avvio:

1. Estrai lo ZIP e trascina `CleanSlate.app` in Applicazioni.
2. Aprila. Se macOS la blocca, vai in Impostazioni di Sistema → Privacy e sicurezza e scegli **Apri comunque**.
3. Fallo solo se ti fidi della provenienza. Non serve disattivare Gatekeeper né usare il Terminale.
4. Al primo uso di un profilo IMAP salvato, macOS può chiedere il permesso di accedere al Portachiavi.

Per controllare il file scaricato c'è l'impronta SHA-256 accanto allo ZIP; è un controllo di integrità, non una firma dell'autore. Guida Apple: <https://support.apple.com/it-it/102445>.

## Licenza

GPL-3.0 (le librerie incluse mantengono le proprie licenze; i moduli OSINT derivano da Holehe, anch'essa GPL-3.0). Testi e crediti: `LICENSE` e `THIRD_PARTY_NOTICES.md`.

## Link (segnaposto: da compilare dopo la pubblicazione)

- Repository: `[LINK-REPOSITORY — da definire]`
- Download (release con ZIP, SHA-256 e note): `[LINK-DOWNLOAD — da definire]`

## Catture (`.officina/galleria/sito/`)

| File | Mostra |
|---|---|
| `01-avvio.png` | Schermata iniziale con la scheda OSINT |
| `02-imap.png` | Scheda IMAP con i profili salvati nel Portachiavi |
| `03-risultati.png` | Risultati con i Dati Demo: 8 servizi, riepilogo e filtri |
| `04-gdpr.png` | Generatore della richiesta Art. 17 GDPR |

Le catture mostrano l'interfaccia web dai sorgenti (la stessa che si vede nell'app) con indirizzo e nome fittizi (`alex.rossi@example.com`, «Mario Rossi»). Non sono catture della finestra nativa dell'app macOS.
