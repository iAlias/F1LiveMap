"""Coordinator del calendario F1."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
import logging

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    CALENDARIO_URL,
    CONF_ANTICIPO,
    CONF_EXTRA,
    DEFAULT_ANTICIPO,
    DEFAULT_EXTRA,
    DOMAIN,
    NOME,
)
from .sessions import Sessione, parse_calendario, stato

_LOGGER = logging.getLogger(__name__)


class F1Coordinator(DataUpdateCoordinator[list[Sessione]]):
    """Scarica il calendario della stagione e calcola lo stato delle sessioni."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            config_entry=entry,
            update_interval=timedelta(hours=12),
        )
        self.device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=NOME,
            entry_type=DeviceEntryType.SERVICE,
        )

    async def _async_update_data(self) -> list[Sessione]:
        try:
            async with asyncio.timeout(30):
                risposta = await async_get_clientsession(self.hass).get(CALENDARIO_URL)
                risposta.raise_for_status()
                return parse_calendario(await risposta.json(content_type=None))
        except (aiohttp.ClientError, TimeoutError, ValueError) as err:
            if self.data is not None:
                _LOGGER.warning("Calendario F1 non aggiornato, uso l'ultimo valido: %s", err)
                return self.data
            raise UpdateFailed(f"Calendario F1 non disponibile: {err}") from err

    def stato_attuale(self) -> tuple[Sessione | None, Sessione | None]:
        """Restituisce (sessione in corso, prossima sessione) per l'ora corrente."""
        opzioni = self.config_entry.options
        return stato(
            self.data,
            dt_util.utcnow(),
            timedelta(minutes=opzioni.get(CONF_ANTICIPO, DEFAULT_ANTICIPO)),
            timedelta(minutes=opzioni.get(CONF_EXTRA, DEFAULT_EXTRA)),
        )

    @callback
    def tick(self, _adesso: datetime) -> None:
        """Fa ricalcolare lo stato alle entità senza richieste di rete."""
        self.async_update_listeners()
