"""Sensore binario: sessione F1 in corso."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import F1Coordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([SessioneInCorso(entry.runtime_data)])


class SessioneInCorso(CoordinatorEntity[F1Coordinator], BinarySensorEntity):
    """Acceso durante la finestra di una sessione."""

    _attr_has_entity_name = True
    _attr_translation_key = "sessione_in_corso"
    _attr_icon = "mdi:racing-helmet"

    def __init__(self, coordinator: F1Coordinator) -> None:
        super().__init__(coordinator)
        # ID fisso: è il default delle card, che così funzionano senza configurazione.
        self.entity_id = "binary_sensor.f1_sessione_in_corso"
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_sessione_in_corso"
        self._attr_device_info = coordinator.device_info

    @property
    def is_on(self) -> bool:
        return self.coordinator.stato_attuale()[0] is not None

    @property
    def extra_state_attributes(self) -> dict[str, str] | None:
        """Sessione in corso se acceso, altrimenti la prossima."""
        in_corso, prossima = self.coordinator.stato_attuale()
        sessione = in_corso or prossima
        return sessione.attributi() if sessione else None
