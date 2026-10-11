from datetime import datetime, timedelta, timezone

import pytest
from sessions import parse_calendario, stato

ZERO = timedelta(0)
ANTICIPO = timedelta(minutes=15)
EXTRA = timedelta(minutes=30)

CALENDARIO = {
    "MRData": {
        "RaceTable": {
            "Races": [
                {
                    "raceName": "Australian Grand Prix",
                    "Circuit": {"circuitName": "Albert Park Grand Prix Circuit"},
                    "date": "2026-03-08",
                    "time": "04:00:00Z",
                    "FirstPractice": {"date": "2026-03-06", "time": "01:30:00Z"},
                    "SecondPractice": {"date": "2026-03-06", "time": "05:00:00Z"},
                    "ThirdPractice": {"date": "2026-03-07", "time": "01:30:00Z"},
                    "Qualifying": {"date": "2026-03-07", "time": "05:00:00Z"},
                },
                {
                    "raceName": "Chinese Grand Prix",
                    "Circuit": {"circuitName": "Shanghai International Circuit"},
                    "date": "2026-03-15",
                    "time": "07:00:00Z",
                    "FirstPractice": {"date": "2026-03-13", "time": "03:30:00Z"},
                    "Qualifying": {"date": "2026-03-14", "time": "07:00:00Z"},
                    "Sprint": {"date": "2026-03-14", "time": "03:00:00Z"},
                    "SprintQualifying": {"date": "2026-03-13", "time": "07:30:00Z"},
                },
                {
                    "raceName": "Japanese Grand Prix",
                    "Circuit": {"circuitName": "Suzuka Circuit"},
                    "date": "2026-03-29",
                    "FirstPractice": {"date": "2026-03-27"},
                },
            ]
        }
    }
}


def utc(*args):
    return datetime(*args, tzinfo=timezone.utc)


@pytest.fixture
def sessioni():
    return parse_calendario(CALENDARIO)


def test_parse_ordina_e_scarta_le_sessioni_senza_orario(sessioni):
    assert len(sessioni) == 10
    assert sessioni == sorted(sessioni, key=lambda s: s.inizio)
    assert all(s.gran_premio != "Japanese Grand Prix" for s in sessioni)
    prima = sessioni[0]
    assert (prima.gran_premio, prima.circuito, prima.tipo, prima.inizio) == (
        "Australian Grand Prix",
        "Albert Park Grand Prix Circuit",
        "Prove libere 1",
        utc(2026, 3, 6, 1, 30),
    )


def test_parse_weekend_sprint(sessioni):
    cina = [s.tipo for s in sessioni if s.gran_premio == "Chinese Grand Prix"]
    assert cina == ["Prove libere 1", "Qualifiche Sprint", "Sprint", "Qualifiche", "Gara"]


def test_parse_calendario_vuoto_e_malformato():
    assert parse_calendario({"MRData": {"RaceTable": {"Races": []}}}) == []
    with pytest.raises(ValueError):
        parse_calendario({"errore": "non è un calendario"})
    with pytest.raises(ValueError):
        parse_calendario(None)


def test_gara_in_corso_e_prossima(sessioni):
    in_corso, prossima = stato(sessioni, utc(2026, 3, 8, 5, 0), ZERO, ZERO)
    assert (in_corso.gran_premio, in_corso.tipo) == ("Australian Grand Prix", "Gara")
    assert (prossima.gran_premio, prossima.tipo) == ("Chinese Grand Prix", "Prove libere 1")


def test_durata_gara_120_altre_60(sessioni):
    # Gara Australia 04:00 -> 06:00, FP1 Australia 01:30 -> 02:30
    assert stato(sessioni, utc(2026, 3, 8, 5, 59), ZERO, ZERO)[0] is not None
    assert stato(sessioni, utc(2026, 3, 8, 6, 0), ZERO, ZERO)[0] is None
    assert stato(sessioni, utc(2026, 3, 6, 2, 29), ZERO, ZERO)[0] is not None
    assert stato(sessioni, utc(2026, 3, 6, 2, 30), ZERO, ZERO)[0] is None


def test_anticipo_ed_extra_allargano_la_finestra(sessioni):
    prima = utc(2026, 3, 8, 3, 50)
    dopo = utc(2026, 3, 8, 6, 20)
    assert stato(sessioni, prima, ZERO, ZERO)[0] is None
    assert stato(sessioni, prima, ANTICIPO, EXTRA)[0].tipo == "Gara"
    assert stato(sessioni, dopo, ZERO, ZERO)[0] is None
    assert stato(sessioni, dopo, ANTICIPO, EXTRA)[0].tipo == "Gara"
    # Durante l'anticipo la sessione non è ancora iniziata: resta anche "prossima".
    assert stato(sessioni, prima, ANTICIPO, EXTRA)[1].tipo == "Gara"


def test_fuori_sessione_e_fine_stagione(sessioni):
    in_corso, prossima = stato(sessioni, utc(2026, 3, 10, 12, 0), ANTICIPO, EXTRA)
    assert in_corso is None
    assert prossima.gran_premio == "Chinese Grand Prix"
    assert stato(sessioni, utc(2026, 12, 31), ANTICIPO, EXTRA) == (None, None)
    assert stato([], utc(2026, 3, 8, 5, 0), ANTICIPO, EXTRA) == (None, None)


def test_attributi(sessioni):
    assert sessioni[0].attributi() == {
        "gran_premio": "Australian Grand Prix",
        "sessione": "Prove libere 1",
        "circuito": "Albert Park Grand Prix Circuit",
        "inizio": "2026-03-06T01:30:00+00:00",
    }
