# F1 Live Map

Integrazione per Home Assistant che porta in dashboard la Formula 1 in diretta: durante prove
libere, qualifiche, sprint e gara le card mostrano la mappa del circuito con le posizioni dei
piloti, la classifica, i tempi e le altre informazioni di [f1dash.net](https://f1dash.net).
Fuori sessione mostrano il prossimo appuntamento con il conto alla rovescia.

Non serve nessun account né abbonamento.

## Installazione

1. In HACS apri il menu in alto a destra e scegli **Repository personalizzati**.
2. Aggiungi `https://github.com/iAlias/F1LiveMap` con categoria **Integrazione**.
3. Installa **F1 Live Map** e riavvia Home Assistant.
4. Vai in **Impostazioni → Dispositivi e servizi → Aggiungi integrazione**, cerca
   **F1 Live Map** e conferma.

## Card

Modifica una dashboard, premi **Aggiungi scheda** e cerca "F1". Le card funzionano appena
aggiunte, senza scrivere YAML.

| Card | Cosa mostra |
|---|---|
| **F1 Mappa live** | La mappa del circuito con le posizioni dei piloti in diretta. Il passaggio tra vista 2D, 3D e satellite si fa con i pulsanti dentro la mappa. |
| **F1 Dashboard live** | La dashboard completa: classifica, tempi, distacchi, team radio, direzione gara. |
| **F1 Prossima sessione** | Gran premio, tipo di sessione, data e ora locali, conto alla rovescia. |

Le due card live si attivano da sole quando c'è una sessione. Negli altri momenti mostrano la
prossima sessione e il pulsante **Apri comunque**.

Opzioni delle card live, modificabili dall'editor visuale:

- **Altezza**: altezza del riquadro in pixel. La pagina incorporata ha una propria intestazione
  sopra la mappa: se la mappa risulta tagliata, aumenta questo valore.
- **Mostra sempre**: tiene la mappa o la dashboard visibile anche fuori sessione.
- **Nascondi il banner dei cookie** (attivo): taglia via la fascia inferiore della pagina
  incorporata, dove f1dash.net mostra la richiesta sui cookie. Il banner resta senza risposta,
  non viene accettato al posto tuo. Insieme al banner sparisce tutto ciò che il sito ancora al
  fondo della sua finestra, e gli ultimi 200-300 pixel della pagina non sono raggiungibili
  scorrendo: se ti serve vederli, aumenta l'altezza o disattiva l'opzione.

Sotto il riquadro, **Schermo intero** porta la card a tutto schermo; lo stesso pulsante riporta
alla dashboard. Sui dispositivi che non consentono lo schermo intero vero (ad esempio iPhone)
la card occupa comunque tutta la finestra.

Se dopo l'installazione le card non compaiono nel selettore, svuota la cache del browser e
ricarica la pagina.

## Entità

| Entità | Descrizione |
|---|---|
| `binary_sensor.f1_sessione_in_corso` | Acceso durante una sessione. Negli attributi trovi gran premio, sessione, circuito e ora di inizio. |
| `sensor.f1_prossima_sessione` | Data e ora di inizio della prossima sessione. |

Puoi usarle nelle automazioni, ad esempio per ricevere una notifica quando inizia la gara.

## Opzioni

Da **Impostazioni → Dispositivi e servizi → F1 Live Map → Configura**:

- **Minuti di anticipo** (predefinito 15): quanto prima dell'inizio la sessione risulta in corso.
- **Minuti extra dopo la fine** (predefinito 30): margine per ritardi e bandiere rosse.

## Limiti

- Il calendario indica l'ora di inizio delle sessioni ma non quella di fine. L'integrazione
  considera 120 minuti per la gara e 60 per le altre sessioni, più i minuti extra. Se una
  sessione dura molto più del previsto la card può chiudersi prima: aumenta i minuti extra o
  usa **Apri comunque**.
- Mappa e dashboard sono le pagine di f1dash.net incorporate nella card: contenuti, lingua e
  pubblicità sono quelli del sito. I team radio sono in inglese.
- Se f1dash.net non è raggiungibile o smette di consentire l'incorporamento, le card live non
  possono mostrare nulla; resta il link **Apri in una nuova scheda**.

## Fonti dei dati

- Calendario: [Jolpica F1 API](https://github.com/jolpica/jolpica-f1).
- Mappa e dati live: [f1dash.net](https://f1dash.net).

Progetto non ufficiale, non affiliato a Formula 1, FIA, f1dash.net o Jolpica. F1 e Formula 1
sono marchi di Formula One Licensing B.V.
