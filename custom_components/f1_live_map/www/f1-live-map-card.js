/* F1 Live Map: card Lovelace. JavaScript vanilla, nessuna build. */

const F1DASH = "https://f1dash.net";
const ENTITA = "binary_sensor.f1_sessione_in_corso";

const TESTI = {
  it: {
    prossima: "Prossima sessione",
    in_corso: "In corso",
    nessuna: "Nessuna sessione in programma",
    manca: "Dati F1 non disponibili: controlla che l'integrazione F1 Live Map sia installata e attiva.",
    apri: "Apri comunque",
    nuova: "Apri in una nuova scheda",
    tra: "tra",
    unita: ["g", "h", "min"],
    entity: "Entità",
    altezza: "Altezza",
    mostra_sempre: "Mostra sempre, anche fuori sessione",
    nascondi_cookie: "Nascondi il banner dei cookie",
    schermo_intero: "Schermo intero",
    esci: "Esci da schermo intero",
  },
  en: {
    prossima: "Next session",
    in_corso: "Live",
    nessuna: "No upcoming session",
    manca: "F1 data unavailable: check that the F1 Live Map integration is installed and running.",
    apri: "Open anyway",
    nuova: "Open in a new tab",
    tra: "in",
    unita: ["d", "h", "min"],
    entity: "Entity",
    altezza: "Height",
    mostra_sempre: "Always show, even outside sessions",
    nascondi_cookie: "Hide the cookie banner",
    schermo_intero: "Full screen",
    esci: "Exit full screen",
  },
};

const STILE = `
  :host { display: block; }
  :host(.pieno) { position: fixed; inset: 0; z-index: 9999; }
  :host(:fullscreen), :host(.pieno) { background: var(--card-background-color, #111); }
  ha-card { overflow: hidden; }
  :host(:fullscreen) ha-card, :host(.pieno) ha-card {
    display: flex; flex-direction: column; height: 100%; border-radius: 0;
  }
  .cornice {
    position: relative; overflow: hidden; height: var(--altezza);
    container-type: inline-size;
  }
  :host(:fullscreen) .cornice, :host(.pieno) .cornice { flex: 1; height: auto; }
  iframe { position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: 0; }
  /* ponytail: il CSS non può entrare in un iframe di un altro sito. Il banner cookie di
     f1dash è ancorato al fondo della sua finestra, quindi allungo l'iframe oltre la cornice
     e lo taglio via. Misure prese l'11/10/2026 (200 px da 480 in su, fino a 298 sotto):
     se f1dash cambia il banner vanno riprese. */
  .taglia iframe { height: calc(100% + 210px); }
  @container (max-width: 479px) {
    .taglia iframe { height: calc(100% + 300px); }
  }
  .piede {
    display: flex; justify-content: flex-end; gap: 16px;
    padding: 6px 16px; font-size: 12px;
  }
  .piede button {
    margin: 0; padding: 0; border: 0; border-radius: 0;
    font-size: inherit; text-decoration: underline;
  }
  .esci, :host(:fullscreen) .entra, :host(.pieno) .entra { display: none; }
  :host(:fullscreen) .esci, :host(.pieno) .esci { display: inline; }
  a { color: var(--primary-color); }
  .corpo { display: flex; flex-direction: column; gap: 4px; padding: 16px; }
  .etichetta {
    font-size: 12px; letter-spacing: 0.08em; text-transform: uppercase;
    color: var(--secondary-text-color);
  }
  .titolo { font-size: 20px; font-weight: 500; }
  .quando, .avviso { color: var(--secondary-text-color); }
  .conto { margin-top: 8px; font-size: 28px; font-variant-numeric: tabular-nums; }
  button {
    align-self: flex-start; margin-top: 12px; padding: 8px 16px;
    border: 1px solid var(--divider-color); border-radius: 8px;
    background: none; color: var(--primary-color); font: inherit; cursor: pointer;
  }
`;

const testi = (lingua) => TESTI[(lingua || "").slice(0, 2)] || TESTI.en;

function el(tag, classe, testo) {
  const nodo = document.createElement(tag);
  if (classe) nodo.className = classe;
  if (testo != null) nodo.textContent = testo;
  return nodo;
}

function contoAllaRovescia(ms, [g, h, m]) {
  const minuti = Math.max(0, Math.ceil(ms / 60000));
  const giorni = Math.floor(minuti / 1440);
  const ore = Math.floor((minuti % 1440) / 60);
  return [giorni && `${giorni} ${g}`, (giorni || ore) && `${ore} ${h}`, `${minuti % 60} ${m}`]
    .filter(Boolean)
    .join(" ");
}

class F1Card extends HTMLElement {
  static pagina = null; // percorso su f1dash.net; null = solo prossima sessione
  static altezza = 0;

  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._stile = el("style", "", STILE);
  }

  static getStubConfig() {
    return { entity: ENTITA };
  }

  static getConfigForm() {
    const t = testi(document.documentElement.lang);
    return {
      schema: [
        { name: "entity", selector: { entity: { domain: "binary_sensor" } } },
        ...(this.pagina
          ? [
              {
                name: "altezza",
                selector: {
                  number: { min: 200, max: 2000, step: 10, mode: "box", unit_of_measurement: "px" },
                },
              },
              { name: "mostra_sempre", selector: { boolean: {} } },
              { name: "nascondi_cookie", selector: { boolean: {} } },
            ]
          : []),
      ],
      computeLabel: (campo) => t[campo.name],
    };
  }

  setConfig(config) {
    this._config = {
      mostra_sempre: false,
      nascondi_cookie: true,
      ...config,
      entity: config.entity || ENTITA,
      altezza: Number(config.altezza) || this.constructor.altezza,
    };
    this._firma = null;
    this._aggiorna();
  }

  set hass(hass) {
    this._hass = hass;
    this._aggiorna();
  }

  connectedCallback() {
    // Il conto alla rovescia avanza anche quando lo stato dell'entità non cambia.
    this._timer = setInterval(() => this._aggiorna(), 30000);
  }

  disconnectedCallback() {
    clearInterval(this._timer);
  }

  getCardSize() {
    return this._live ? Math.ceil(this._config.altezza / 50) : 3;
  }

  _esciSchermoIntero() {
    if (this.matches(":fullscreen")) document.exitFullscreen();
    this.classList.remove("pieno");
  }

  async _schermoIntero() {
    if (this.matches(":fullscreen") || this.classList.contains("pieno")) {
      return this._esciSchermoIntero();
    }
    try {
      await this.requestFullscreen();
    } catch {
      // ponytail: senza Fullscreen API (iPhone, alcune webview) ripiego su position: fixed.
      // Un antenato con transform o contain può ritagliarlo: in quel caso serve il top
      // layer (attributo popover).
      this.classList.add("pieno");
    }
  }

  _righe(stato, t, lingua) {
    if (!stato || stato.state === "unavailable") return [["avviso", t.manca]];
    const inizio = new Date(stato.attributes.inizio);
    if (isNaN(inizio)) return [["titolo", t.nessuna]];
    const inCorso = stato.state === "on";
    const righe = [
      ["etichetta", inCorso ? t.in_corso : t.prossima],
      ["titolo", stato.attributes.gran_premio],
      ["sessione", stato.attributes.sessione],
      [
        "quando",
        inizio.toLocaleString(lingua, {
          weekday: "long",
          day: "numeric",
          month: "long",
          hour: "2-digit",
          minute: "2-digit",
        }),
      ],
    ];
    if (!inCorso) righe.push(["conto", `${t.tra} ${contoAllaRovescia(inizio - Date.now(), t.unita)}`]);
    return righe;
  }

  _aggiorna() {
    if (!this._config || !this._hass) return;
    const lingua = this._hass.locale?.language || this._hass.language;
    const t = testi(lingua);
    const stato = this._hass.states[this._config.entity];
    const pagina = this.constructor.pagina;
    this._live = Boolean(
      pagina && (this._config.mostra_sempre || this._forzato || stato?.state === "on")
    );
    const righe = this._live ? [] : this._righe(stato, t, lingua);

    // hass arriva di continuo: ridisegno solo se cambia ciò che si vede, così
    // l'iframe non viene ricaricato a ogni aggiornamento di stato.
    const firma = JSON.stringify([this._live, this._config, righe]);
    if (firma === this._firma) return;
    this._firma = firma;

    const card = el("ha-card");
    if (this._live) {
      const url = F1DASH + pagina;
      const iframe = el("iframe");
      // Senza allow-top-navigation il sito non può reindirizzare la scheda di HA.
      iframe.setAttribute("sandbox", "allow-scripts allow-same-origin allow-popups allow-forms");
      iframe.setAttribute("allow", "fullscreen");
      iframe.referrerPolicy = "no-referrer";
      iframe.title = "F1Dash";
      iframe.src = url;
      const cornice = el("div", this._config.nascondi_cookie ? "cornice taglia" : "cornice");
      cornice.style.setProperty("--altezza", `${this._config.altezza}px`);
      cornice.append(iframe);
      const schermo = el("button");
      schermo.append(el("span", "entra", t.schermo_intero), el("span", "esci", t.esci));
      schermo.addEventListener("click", () => this._schermoIntero());
      const link = el("a", "", t.nuova);
      link.href = url;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      const piede = el("div", "piede");
      piede.append(schermo, link);
      card.append(cornice, piede);
    } else {
      this._esciSchermoIntero();
      const corpo = el("div", "corpo");
      // textContent, mai innerHTML: i nomi arrivano da un'API esterna.
      for (const [classe, testo] of righe) corpo.append(el("div", classe, testo));
      if (pagina) {
        const bottone = el("button", "", t.apri);
        bottone.addEventListener("click", () => {
          this._forzato = true;
          this._aggiorna();
        });
        corpo.append(bottone);
      }
      card.append(corpo);
    }
    this.shadowRoot.replaceChildren(this._stile, card);
  }
}

// All'avvio il frontend di HA sostituisce window.customElements con un registro nuovo
// (polyfill dei registri "scoped"). Questo file viene caricato in parallelo all'app: le
// card definite prima della sostituzione spariscono da customElements.get() e il selettore
// risponde "Custom element not found". Quindi si definiscono solo ad app partita.
const appPronta = customElements.whenDefined("home-assistant");

function registra(tag, pagina, altezza, nome, descrizione) {
  const classe = class extends F1Card {
    static pagina = pagina;
    static altezza = altezza;
  };
  appPronta.then(() => customElements.define(tag, classe));
  (window.customCards ||= []).push({
    type: tag,
    name: nome,
    description: descrizione,
    // Niente anteprima per le card live: caricherebbe f1dash dentro il selettore.
    preview: !pagina,
    documentationURL: "https://github.com/iAlias/F1LiveMap",
  });
}

registra(
  "f1-live-map-card",
  "/map",
  600,
  "F1 Mappa live",
  "Mappa del circuito con le posizioni dei piloti in diretta (f1dash.net)."
);
registra(
  "f1-live-dashboard-card",
  "/dashboard",
  900,
  "F1 Dashboard live",
  "Classifica, tempi, team radio e direzione gara in diretta (f1dash.net)."
);
registra(
  "f1-next-session-card",
  null,
  0,
  "F1 Prossima sessione",
  "Gran premio, tipo di sessione e conto alla rovescia."
);
