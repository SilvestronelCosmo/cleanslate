# CleanSlate 1.0.0 — note di rilascio

Stato: **pronto per il rilascio** (01/10/2026): funzioni, verifiche, licenza e requisiti completati; manca solo il tag Git, che si crea dopo il commit approvato. La versione 1.0.0 è indicata nel pacchetto Python, nell'API e nel bundle macOS.

## Funzioni incluse

- Ricerca OSINT su 16 servizi. Per ogni servizio che non dà una risposta verificabile l'app mostra la causa osservata (errore HTTP, tempo scaduto, limite di richieste) separata dall'ipotesi; il dettaglio dell'indagine è in [docs/osint-servizi.md](docs/osint-servizi.md).
- Scansione degli header di una casella IMAP o di un archivio MBOX, con classificazione di account, abbonamenti e newsletter, e un cronometro che mostra il tempo reale della scansione.
- Profili IMAP salvati: server, porta e utente nel profilo, password solo nel Portachiavi di macOS; l'ultimo profilo usato si riapre all'avvio.
- Collegamenti per la chiusura degli account, disiscrizione compatibile con RFC 8058 e modello di richiesta di cancellazione dei dati.
- Interfaccia web locale, app macOS (nella barra dei menu si chiama «CleanSlate») e dati dimostrativi utilizzabili senza credenziali.

## Riscontro della prova nell'app

Nella prova del 1° ottobre 2026, Pietro ha riferito che OSINT ha segnalato **2 account**. Ha inoltre visto **9 servizi non verificabili**: Deliveroo, SoundCloud, Pinterest, Patreon, Discord, GitHub, Tumblr, Snapchat e Strava. Per questi servizi l'app non può concludere se esista o meno un account: gli endpoint esterni possono restituire errori, cambiare comportamento o limitare le richieste. Il risultato varia nel tempo e secondo la rete.

La scansione IMAP di Pietro è riuscita. Nelle prove del 1° ottobre 2026 ha osservato:

| Messaggi esaminati | Durata misurata | Servizi rilevati |
| --- | --- | --- |
| 150 email | 32 s | 28 servizi |
| 350 email | 1 min 9 s | 49 servizi |
| 750 email | 2 min 23 s | 74 servizi |

Sono misure di queste prove, non stime garantite: la durata dipende dalla casella, dal provider e dalla connessione. Le vecchie durate indicate nelle opzioni sottostimavano quelle osservate e sono state rimosse. Durante la scansione l'app mostra il tempo trascorso e, al termine, la durata effettiva del tentativo. Nessun indirizzo o credenziale personale è riportato.

## Limiti noti

- Le verifiche OSINT dipendono da servizi esterni e da moduli Holehe; un servizio non verificabile non è un risultato negativo. Otto servizi restano «non determinati» (vedi [docs/osint-servizi.md](docs/osint-servizi.md)).
- La scansione IMAP legge gli header degli ultimi messaggi selezionati e richiede un accesso IMAP valido; alcuni provider richiedono una password per le app. Niente OAuth.
- Il salvataggio delle password funziona solo su macOS (Portachiavi); sugli altri sistemi la password si inserisce a ogni scansione.
- IMAP verifica sempre il certificato e il nome del server. I server con certificato autofirmato (per esempio i bridge locali) non sono supportati: la connessione viene rifiutata e non esiste un'opzione per disattivare il controllo.
- Il pacchetto per Mac è un'app autonoma (Apple Silicon), non firmata né notarizzata: al primo avvio macOS può chiedere «Apri comunque» (vedi [docs/INSTALLAZIONE_MACOS.md](docs/INSTALLAZIONE_MACOS.md)).

## Licenza

GPL-3.0 (per la dipendenza Holehe); crediti e licenze delle dipendenze in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
