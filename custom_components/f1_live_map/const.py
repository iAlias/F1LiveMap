"""Costanti dell'integrazione F1 Live Map."""

DOMAIN = "f1_live_map"
NOME = "F1 Live Map"

CALENDARIO_URL = "https://api.jolpi.ca/ergast/f1/current.json?limit=100"

CONF_ANTICIPO = "anticipo_minuti"
CONF_EXTRA = "extra_minuti"
DEFAULT_ANTICIPO = 15
DEFAULT_EXTRA = 30

CARD_FILE = "f1-live-map-card.js"
CARD_URL = f"/{DOMAIN}/{CARD_FILE}"
