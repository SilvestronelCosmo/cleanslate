# Indagine OSINT — fase B, 1 ottobre 2026


## Metodo e limiti

Prova eseguita il **2026-10-01**, conclusa alle **10:08:37 UTC**, con **Holehe 1.61**, indirizzo fittizio **`nessuno@example.com`**, senza credenziali. Comando ripetibile dalla radice: `venv/bin/python scripts/diagnose_osint.py`. Lo script esegue gli otto moduli installati e la ricerca pubblica GitHub, in sequenza, con timeout di 6 secondi per richiesta e 20 per modulo. Non salva corpi, cookie, header di autenticazione o token. Non usa servizi a pagamento.

Il primo tentativo nella sandbox non ha ottenuto alcuna risposta HTTP: sei moduli e GitHub hanno sollevato `ConnectError`; Patreon e Tumblr hanno assorbito l'errore e restituito `rateLimit=True`. Il secondo tentativo con accesso alla rete ha prodotto gli esiti della tabella. Questo dimostra anche perché il flag di Holehe **non prova da solo un limite di richieste**.

Gli endpoint sono stati letti nel codice installato sotto `venv/lib/python3.*/site-packages/holehe/modules/`. In tabella sono separati i passaggi previsti dal modulo da quelli effettivamente raggiunti. Un singolo 403/404, un errore del parser o una connessione fallita non dimostrano l'impossibilità di ripristinare il servizio. Non sono stati tentati aggiramenti di captcha, rotazioni IP, nuove registrazioni intenzionali o accessi autenticati. Un risultato negativo con un indirizzo fittizio non prova la capacità di trovare un account reale.

## Otto moduli Holehe

| Servizio | Endpoint usati dal modulo | Esito osservato il 2026-10-01 | Conclusione e motivazione |
| --- | --- | --- | --- |
| Deliveroo | POST `https://consumer-ow-api.deliveroo.com/orderapp/v1/check-email` | `ConnectError`, nessuna risposta HTTP. | **non determinato**: nessuna prova di rate limit o rimozione dell'endpoint; non è stata isolata la causa della connessione fallita. |
| SoundCloud | GET `https://soundcloud.com/octobersveryown`, poi GET `https://api-auth.soundcloud.com/web-auth/identifier` con client ID estratto | HTTP 307 verso `m.soundcloud.com/octobersveryown`, poi HTTP 200; `IndexError` nell'estrazione. Endpoint identifier non raggiunto. | **non determinato**: lo scraper fallisce sulla pagina ricevuta; non è stata verificata un'estrazione alternativa del client ID. |
| Pinterest | GET `https://www.pinterest.com/_ngjs/resource/EmailExistsResource/get/` | HTTP 403, poi `JSONDecodeError`. | **non determinato**: rifiuto osservato una volta; non prova un blocco persistente, un captcha o un endpoint modificato. |
| Patreon | POST `https://www.patreon.com/api/email/available` | HTTP 404; Holehe restituisce `rateLimit=True`, `exists=False`. | **non determinato**: il 404 è osservato, ma non prova da solo che l'endpoint sia stato rimosso definitivamente; il flag non è una prova di rate limit. |
| Discord | POST `https://discord.com/api/v8/auth/register` | HTTP 400; Holehe restituisce `rateLimit=True`, `exists=False`; il rilevatore non ha trovato la stringa esatta `"captcha-required"`. | **non determinato**: la risposta non ha consentito al modulo di stabilire l'esistenza. Il rilevatore non esclude altre forme di captcha; non si attribuisce il fallimento a un captcha senza prova. |
| Tumblr | GET `https://www.tumblr.com/`, poi GET `/api/v2/radar`, POST `/api/v2/register/account/validate` | Home HTTP 200; Holehe restituisce `rateLimit=True`, `exists=False`. Nessuna richiesta a radar o validate. | **non determinato**: fallimento interno dopo la home e prima della seconda richiesta. Il modulo assorbe l'eccezione; la prova non identifica il passaggio preciso né dimostra un rate limit. |
| Snapchat | GET `https://accounts.snapchat.com`, poi POST `https://accounts.snapchat.com/accounts/merlin/login` | HTTP 301 verso `/accounts/v2/login`, 308 verso `/v2/login`, poi 200 senza `data-xsrf`; `IndexError`. POST non raggiunta. | **non determinato**: il parser attuale non trova il dato richiesto; nessun flusso alternativo è stato verificato. |
| Strava | GET `https://www.strava.com/register/free`, poi GET `https://www.strava.com/athletes/email_unique` | Pagina HTTP 200 senza il pattern CSRF atteso; endpoint email HTTP 404. Il modulo produce due voci `rateLimit=True`. | **non determinato**: sono provati due ostacoli del modulo corrente, ma non l'assenza di un'alternativa funzionante. |

Nessuno degli otto è stato dimostrato recuperabile con una correzione verificata in questa indagine. Nessuno viene dichiarato **non recuperabile**. Il piano approvato esclude nuovi probe per questi servizi: un'eventuale implementazione alternativa richiede un lavoro separato e prove positive/negative affidabili. I moduli restano attivi e le difficoltà sono visibili nei risultati.

## GitHub e quattro probe nativi

GitHub: GET `https://api.github.com/search/users`, query `nessuno@example.com in:email`: **HTTP 200**, `total_count=0`, `incomplete_results=false`. Conclusione: **recuperabile**, nel senso limitato che la ricerca pubblica nativa risponde e il suo esito negativo è distinguibile dagli errori. Non è una verifica delle registrazioni private e non è stato provato un riscontro positivo reale. Holehe GitHub era già escluso prima di questa fase.

La ricerca può essere incompleta; GitHub può rispondere 403/429 per i limiti. La correzione tratta questi casi come non verificabili. Un 403 senza altre evidenze resta «HTTP 403»; il limite è indicato per 429 o 403 con `x-ratelimit-remaining: 0`. Fonti: [ricerca REST GitHub](https://docs.github.com/en/rest/search/search#search-users), [limiti REST GitHub](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api).

Per Gravatar, Duolingo, GitHub e Spotify, i test simulati verificano un risultato positivo, un negativo valido, 403, 429, timeout, eccezione, JSON invalido e campi mancanti. Spotify considera negativi soltanto `status=1`, positivi `status=20`; gli altri status sono indeterminati. GitHub non considera un JSON vuoto una ricerca negativa e segnala `incomplete_results=true`. I timeout sono per singolo probe/modulo e non scartano gli altri risultati completati.

Come richiesto dalla fase B, ogni HTTP diverso da 200 dei probe nativi viene segnalato come non verificabile. Per Gravatar resta l'endpoint legacy `en.gravatar.com/{md5}.json`; nessuna migrazione all'API v3 è stata eseguita. La documentazione della [API Gravatar v3](https://docs.gravatar.com/rest-api/) descrive il 404 come profilo non trovato, ma questo non viene trasferito automaticamente al contratto legacy. Il comportamento conservativo non equivale a un account assente.

## Contratto e modifiche

- Ogni non verificabile ha `domain` e `cause` osservata: codice HTTP, tipo di eccezione o flag `rateLimit=True` restituito dal modulo. `hint` è soltanto un'ipotesi condizionale, visualizzata come «Possibile causa». `reason` resta alias di `cause` per compatibilità con i precedenti client API.
- I moduli Holehe che catturano internamente gli errori conservano una diagnostica limitata al flag restituito: la scansione ordinaria non inventa un HTTP o un'eccezione che il modulo non comunica. Lo script d'indagine raccoglie separatamente gli status HTTP.
- I domini di ripiego sono mappati esplicitamente, compresi `proton.me`, `last.fm` e `docker.com`. I dettagli d'eccezione potenzialmente contenenti indirizzi o token non vengono esposti.
- La CLI stampa `dominio (causa)`; l'interfaccia mostra un avviso breve e dettagli espandibili con testo escapato. Le ipotesi non vengono stampate come cause.

Limiti letti nei moduli, non risolti da questa fase: SoundCloud contiene una condizione sempre vera (`status == 'available' or 'in_use'`); Discord può interpretare `captcha-required` come negativo; Snapchat costruisce il corpo JSON della POST senza virgolette intorno all'email. Sono difetti nel codice della dipendenza; nessuna modifica a vendor è stata applicata, e nella prova sopra quei rami non hanno fornito un esito affidabile. La classificazione «nessun riscontro» di Holehe non è quindi una certificazione universale di account assente.
