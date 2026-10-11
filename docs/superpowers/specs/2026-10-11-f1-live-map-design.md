# F1 Live Map — design

Data: 2026-10-11 · Stato: in attesa di revisione

## Obiettivo

Un'integrazione HACS per Home Assistant che, durante prove libere, qualifiche, sprint e gara,
mostra in dashboard la mappa live del circuito (2D/3D), le posizioni dei piloti, i tempi e le
altre informazioni di f1dash.net. Si configura aggiungendo card già pronte dal selettore card,
senza scrivere YAML.

## Decisioni prese

- **La parte live è un embed di f1dash.net** in iframe, non un rendering proprio. Motivo: le
  posizioni delle auto e i team radio del feed ufficiale F1 richiedono un token F1 TV; l'embed
  li mostra senza abbonamenti.
- **Il calendario viene da Jolpica** (`https://api.jolpi.ca/ergast/f1/current.json?limit=100`),
  gratuito e senza chiave. Serve a sapere quando c'è una sessione.
- **Team radio in italiano: fuori ambito.** Il contenuto di un iframe non è modificabile, quindi
  i team radio restano in inglese come li mostra f1dash. La traduzione richiederebbe token F1 TV
  e un servizio di trascrizione; è un'estensione successiva, non parte di questa spec.

## Fuori ambito

Team radio tradotti, classifiche mondiali, risultati storici, replay, rendering proprio della
mappa, scelta 2D/3D da configurazione (si cambia con i comandi di f1dash dentro la card).

## Struttura

Repository indipendente nella cartella `F1 Live Map`, dominio `f1_live_map`, nome "F1 Live Map".

```
custom_components/f1_live_map/
  __init__.py          setup/unload, registrazione del file JS della card
  manifest.json        config_flow: true, single_config_entry: true,
                       dependencies: ["http", "frontend"], iot_class: cloud_polling
  const.py             dominio, URL, chiavi e default delle opzioni (le durate stanno in
                       sessions.py, che deve restare importabile da solo)
  config_flow.py       flusso a un passaggio + flusso opzioni
  coordinator.py       DataUpdateCoordinator sul calendario
  sessions.py          logica pura, senza import di Home Assistant
  binary_sensor.py     sessione in corso
  sensor.py            prossima sessione
  strings.json
  translations/it.json
  translations/en.json
  www/f1-live-map-card.js
tests/
  conftest.py          carica sessions.py senza eseguire __init__.py
  test_sessions.py
.github/workflows/validate.yml
hacs.json
README.md              in italiano, per l'utente finale
LICENSE                MIT
```

## Logica delle sessioni (`sessions.py`)

Due funzioni pure:

- `parse_calendario(json) -> list[Sessione]`: per ogni gara produce una `Sessione`
  (`gran_premio`, `circuito`, `tipo`, `inizio` in UTC) per ciascuna chiave presente tra
  `FirstPractice`, `SecondPractice`, `ThirdPractice`, `SprintQualifying`, `Sprint`,
  `Qualifying` e la gara stessa (`date`/`time` al livello della gara). Le sessioni senza
  orario vengono scartate. Risultato ordinato per `inizio`.
- `stato(sessioni, adesso, anticipo, extra) -> (in_corso, prossima)`:
  `in_corso` è la sessione per cui `inizio − anticipo <= adesso < inizio + durata + extra`,
  altrimenti `None`; `prossima` è la prima sessione con `inizio > adesso`, altrimenti `None`.

Durate fisse, perché Jolpica non fornisce l'ora di fine: gara 120 minuti, tutte le altre 60.
È un'approssimazione: una bandiera rossa lunga può far chiudere la finestra in anticipo. La
compensano l'opzione `extra` e il pulsante "Apri comunque" della card.

Etichette italiane del tipo: Prove libere 1/2/3, Qualifiche Sprint, Sprint, Qualifiche, Gara.

## Coordinator

- Scarica il calendario ogni 12 ore con la sessione HTTP condivisa di Home Assistant.
- Se il download fallisce e c'è già un calendario valido, lo mantiene e registra un avviso: i
  sensori continuano a funzionare. Solo al primo avvio senza dati solleva `UpdateFailed`.
- A stagione finita `prossima` è `None` finché Jolpica non pubblica il calendario nuovo.

## Entità

Un solo dispositivo "F1 Live Map". Gli ID sono fissi, così le card funzionano senza
configurazione.

| Entità | Stato | Attributi |
|---|---|---|
| `binary_sensor.f1_sessione_in_corso` | `on` durante la finestra di una sessione | `gran_premio`, `sessione`, `circuito`, `inizio`: della sessione in corso se `on`, della prossima se `off` |
| `sensor.f1_prossima_sessione` | data e ora di inizio della prossima sessione (`device_class: timestamp`) | `gran_premio`, `sessione`, `circuito`, `inizio` |

Le entità ricalcolano lo stato ogni minuto dall'ora corrente, senza richieste di rete.

## Configurazione

- Installazione dalla UI in un passaggio, senza campi. Una sola istanza.
- Opzioni: `anticipo_minuti` (default 15, intervallo 0–120) e `extra_minuti` (default 30,
  intervallo 0–240).

## Card (`www/f1-live-map-card.js`)

Un file JavaScript vanilla, senza build né dipendenze. L'integrazione lo espone su
`/f1_live_map/f1-live-map-card.js` e lo aggiunge al frontend all'avvio, con la versione del
manifest in query string per invalidare la cache.

Tre card nel selettore, registrate in `window.customCards` con nome, descrizione e anteprima:

| Tipo | Nome | Contenuto |
|---|---|---|
| `custom:f1-live-map-card` | F1 Mappa live | iframe di `https://f1dash.net/map`, altezza default 600 px |
| `custom:f1-live-dashboard-card` | F1 Dashboard live | iframe di `https://f1dash.net/dashboard`, altezza default 900 px |
| `custom:f1-next-session-card` | F1 Prossima sessione | gran premio, tipo di sessione, data e ora locali, conto alla rovescia |

Comportamento delle due card live:

- Sessione in corso (sensore `on`): mostrano l'iframe.
- Fuori sessione: mostrano il contenuto della card "Prossima sessione" e il pulsante
  "Apri comunque", che carica l'iframe fino al ricaricamento della pagina.
- L'iframe viene creato solo quando serve: fuori sessione non parte nessuna richiesta verso
  f1dash.net.
- Sotto l'iframe c'è sempre il link "Apri in una nuova scheda", utile anche se f1dash dovesse
  bloccare l'embed.
- L'iframe usa `sandbox="allow-scripts allow-same-origin allow-popups allow-forms"`: il sito
  funziona, ma non può reindirizzare la scheda di Home Assistant.

Opzioni, tutte modificabili dall'editor visuale: `entity` (default
`binary_sensor.f1_sessione_in_corso`), `altezza` in pixel, `mostra_sempre` (default no).
L'editor usa il form nativo di Home Assistant tramite `getConfigForm()`. Sulle versioni di
Home Assistant che non lo supportano la card resta configurabile dall'editor YAML; un editor
di ripiego basato su `ha-form` non è stato implementato.

Testi della card in italiano, con inglese come ripiego per le altre lingue.

## Gestione degli errori

| Caso | Comportamento |
|---|---|
| Jolpica non risponde | Si usa l'ultimo calendario valido |
| Entità mancante o non disponibile | La card mostra un messaggio che invita a installare/configurare l'integrazione |
| f1dash blocca l'embed o è irraggiungibile | Resta il link "Apri in una nuova scheda" |
| Nessuna sessione futura in calendario | La card mostra "Nessuna sessione in programma" |

## Verifica

- `python -m pytest tests -q`: sessione in corso, prossima sessione, weekend sprint, effetto di
  anticipo ed extra, calendario vuoto. Solo logica pura, senza Home Assistant né rete.
- CI (`validate.yml`): hassfest, HACS (con `ignore: brands`) e il job pytest. Il job pytest è
  l'unico punto in cui i test girano se in locale manca Python.
- Prova manuale in Home Assistant durante una sessione reale: è l'unico modo di verificare
  l'embed con dati live.

## Dipendenze esterne e rischi

- **f1dash.net** è un sito di terzi, non affiliato. Può cambiare indirizzi, bloccare l'iframe
  o chiudere. I suoi termini d'uso non sono stati letti (pagina renderizzata lato client).
  Dentro la card compaiono la sua pubblicità e il suo banner cookie.
- **Jolpica** è un servizio gratuito della community, senza garanzie di disponibilità.
- Il README dichiara che il progetto non è ufficiale né affiliato a Formula 1 o a f1dash.net.
