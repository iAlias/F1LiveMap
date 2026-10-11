"""Logica pura delle sessioni F1: nessun import di Home Assistant."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

# Chiave Jolpica -> etichetta. La gara non ha una chiave: i suoi date/time stanno
# al livello della gara stessa.
TIPI = {
    "FirstPractice": "Prove libere 1",
    "SecondPractice": "Prove libere 2",
    "ThirdPractice": "Prove libere 3",
    "SprintQualifying": "Qualifiche Sprint",
    "Sprint": "Sprint",
    "Qualifying": "Qualifiche",
}
GARA = "Gara"

# ponytail: durate fisse, Jolpica non dà l'ora di fine. Una bandiera rossa lunga
# sfora la finestra: la compensano l'opzione "extra" e "Apri comunque" nella card.
# Per fare meglio serve lo stato sessione del live timing F1.
DURATA_GARA = timedelta(minutes=120)
DURATA_ALTRE = timedelta(minutes=60)


@dataclass(frozen=True)
class Sessione:
    gran_premio: str
    circuito: str
    tipo: str
    inizio: datetime

    @property
    def durata(self) -> timedelta:
        return DURATA_GARA if self.tipo == GARA else DURATA_ALTRE

    def attributi(self) -> dict[str, str]:
        return {
            "gran_premio": self.gran_premio,
            "sessione": self.tipo,
            "circuito": self.circuito,
            "inizio": self.inizio.isoformat(),
        }


def _inizio(voce) -> datetime | None:
    try:
        inizio = datetime.fromisoformat(f"{voce['date']}T{voce['time']}".replace("Z", "+00:00"))
    except (KeyError, TypeError, ValueError):
        return None
    return inizio if inizio.tzinfo else inizio.replace(tzinfo=timezone.utc)


def parse_calendario(dati) -> list[Sessione]:
    """Converte la risposta Jolpica in sessioni ordinate per inizio.

    Solleva ValueError se la struttura non è quella attesa, così chi chiama può
    distinguere una risposta rotta da un calendario legittimamente vuoto.
    """
    try:
        gare = dati["MRData"]["RaceTable"]["Races"]
    except (KeyError, TypeError) as err:
        raise ValueError("risposta del calendario non valida") from err

    sessioni = []
    for gara in gare:
        gran_premio = gara.get("raceName", "")
        circuito = gara.get("Circuit", {}).get("circuitName", "")
        voci = [(etichetta, gara.get(chiave)) for chiave, etichetta in TIPI.items()]
        voci.append((GARA, gara))
        for tipo, voce in voci:
            if (inizio := _inizio(voce)) is not None:
                sessioni.append(Sessione(gran_premio, circuito, tipo, inizio))
    return sorted(sessioni, key=lambda s: s.inizio)


def stato(
    sessioni: list[Sessione], adesso: datetime, anticipo: timedelta, extra: timedelta
) -> tuple[Sessione | None, Sessione | None]:
    """Restituisce (sessione in corso, prossima sessione); `sessioni` è ordinata."""
    in_corso = next(
        (s for s in sessioni if s.inizio - anticipo <= adesso < s.inizio + s.durata + extra),
        None,
    )
    prossima = next((s for s in sessioni if s.inizio > adesso), None)
    return in_corso, prossima
