# Crediti e licenze di terzi

CleanSlate è distribuito sotto **GNU GPL versione 3 soltanto** (`GPL-3.0-only`); il testo integrale è in [LICENSE](LICENSE). Questa licenza riguarda il codice di CleanSlate. Le librerie installate separatamente conservano i rispettivi titolari e le rispettive licenze. La scelta GPL-3.0 è coerente con l'uso dei moduli Python di Holehe; non implica che CleanSlate sia un progetto di Holehe o dei suoi autori.

Il testo della GPL in `LICENSE` è una copia integrale non modificata della [GNU General Public License v3](https://www.gnu.org/licenses/gpl-3.0.html). La copia locale proviene dal file `COPYING` di una distribuzione Python installata; intestazione e versione corrispondono alla fonte della Free Software Foundation.

## Dipendenze dirette

Inventario di `requirements.txt`, verificato il 1° ottobre 2026 sulle versioni presenti nell'ambiente locale. I vincoli nel file permettono versioni successive: prima di distribuire un pacchetto occorre controllare le versioni effettivamente incluse e le loro note di licenza.


| Libreria | Versione verificata | Licenza | Fonte |
| --- | --- | --- | --- |
| [FastAPI](https://github.com/fastapi/fastapi) | 0.142.2 | MIT | Metadati e `LICENSE` del pacchetto |
| [Uvicorn](https://github.com/Kludex/uvicorn) | 0.54.0 | BSD-3-Clause | Metadati e `LICENSE.md` del pacchetto |
| [HTTPX](https://github.com/encode/httpx) | 0.28.1 | BSD-3-Clause | Metadati del pacchetto |
| [Pydantic](https://github.com/pydantic/pydantic) | 2.13.5 | MIT | Metadati e `LICENSE` del pacchetto |
| [python-multipart](https://github.com/Kludex/python-multipart) | 0.0.32 | Apache-2.0 | Metadati e `LICENSE.txt` del pacchetto |
| [pywebview](https://github.com/r0x0r/pywebview) | 6.2.1 | BSD-3-Clause | Metadati e `LICENSE` del pacchetto |
| [PyObjC Cocoa](https://github.com/ronaldoussoren/pyobjc) | 12.2.2 | MIT | Metadati di pyobjc-framework-Cocoa; solo macOS |
| [Holehe](https://github.com/megadose/holehe) | 1.61 | GPL-3.0 | [Licenza del progetto](https://github.com/megadose/holehe/blob/master/LICENSE.md) e classificatore del pacchetto |
| [pytest](https://github.com/pytest-dev/pytest) | 9.1.1 | MIT | Metadati e `LICENSE` del pacchetto; usato per i test |
| [keyring](https://github.com/jaraco/keyring) | 25.7.0 | MIT | Metadati e `LICENSE` del pacchetto |
| [certifi](https://github.com/certifi/python-certifi) | 2026.7.22 | MPL-2.0 | CA per verifica TLS IMAP; archivio sorgente e licenza inclusi nel pacchetto |

I moduli OSINT importati da Holehe restano codice di Holehe, GNU GPL v3. CleanSlate non conserva una copia dei moduli nel repository: vengono installati come dipendenza Python. I titolari del copyright di Holehe mantengono i loro diritti.

## Directory di cancellazione

[JustDelete.me](https://github.com/jdm-contrib/jdm) è un riferimento per categorie di difficoltà e collegamenti di cancellazione. `cleanslate/core/directory.py` contiene una selezione locale con note e contatti, non una copia dell'intera directory JustDelete.me. Il progetto JustDelete.me è distribuito con [licenza MIT](https://github.com/jdm-contrib/jdm/blob/master/LICENSE); il suo avviso di copyright è: **Copyright (c) 2013-2020 Robb Lewis, The JDM Contrib Team, & various contributors**. JustDelete.me non è affiliato a CleanSlate. I collegamenti e i contatti nella selezione locale possono cambiare: vanno verificati prima dell'uso.

Avviso di licenza di JustDelete.me:

```text
The MIT License (MIT)

Copyright (c) 2013-2020 Robb Lewis, The JDM Contrib Team, & various contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## Pacchetto macOS di prova

La ricetta `scripts/build_macos.py` include nell'app i testi e gli avvisi trovati negli archivi originali delle dipendenze Python e nelle installazioni delle librerie native. Una licenza nativa o Python mancante interrompe la build; per `bs4`, metapacchetto senza codice, si conservano i metadati originali (il codice effettivo appartiene a `beautifulsoup4`).

Lo ZIP contiene i sorgenti CleanSlate e gli archivi PyPI originali di tutte le dipendenze dell'ambiente di build, incluse quelle indirette, con versioni, URL e hash SHA-256. Questo comprende i sorgenti Holehe e i file coperti dalle licenze MPL di certifi e tqdm. Le librerie non vengono modificate. I testi delle licenze e l'inventario sono in `CleanSlate.app/Contents/Resources/legal`; l'elenco dei moduli e binari effettivamente raccolti è in `BUILD-INFO.json`. L'inventario dell'ambiente comprende anche strumenti di sviluppo non incorporati nel runtime.

La tabella delle dipendenze dirette sopra descrive l'ambiente precedente e non sostituisce l'inventario generato. Il pacchetto resta da revisionare prima della pubblicazione; firma Developer ID e notarizzazione non sono eseguite da questa ricetta. Vedere [guida di installazione e ricostruzione](docs/INSTALLAZIONE_MACOS.md).

Eccezioni documentate nella raccolta: lo sdist Holehe 1.61 omette il testo GPL dichiarato nei metadati, quindi si aggiunge la copia GPLv3 integrale presente nel repository. `proxy_tools` 0.1.0 dichiara MIT nei metadati ma BSD nel sorgente e nella licenza upstream: il pacchetto conserva il [testo upstream](https://github.com/jtushman/proxy_tools/blob/ccd35a569b95bec271a59890780c7821756c548a/LICENSE.txt), con entrambi i copyright, senza modificarlo. Fonte e hash sono in `packaging/licenses/PROVENIENZA.txt`.
