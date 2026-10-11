"""Integrazione F1 Live Map."""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.loader import async_get_integration

from .const import CARD_FILE, CARD_URL, DOMAIN
from .coordinator import F1Coordinator

PLATFORMS = [Platform.BINARY_SENSOR, Platform.SENSOR]


async def _registra_card(hass: HomeAssistant) -> None:
    """Espone il JS delle card e lo carica nel frontend, una sola volta per avvio."""
    if hass.data.get(DOMAIN):
        return
    hass.data[DOMAIN] = True
    versione = (await async_get_integration(hass, DOMAIN)).version
    await hass.http.async_register_static_paths(
        [StaticPathConfig(CARD_URL, str(Path(__file__).parent / "www" / CARD_FILE), False)]
    )
    add_extra_js_url(hass, f"{CARD_URL}?v={versione}")


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    await _registra_card(hass)

    coordinator = F1Coordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    # Lo stato dipende dall'ora, non solo dal calendario: ricalcolo ogni minuto.
    entry.async_on_unload(
        async_track_time_interval(hass, coordinator.tick, timedelta(minutes=1))
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
