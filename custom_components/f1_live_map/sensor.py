"""Sensore: inizio della prossima sessione F1."""

from __future__ import annotations

from datetime import datetime

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import F1Coordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([ProssimaSessione(entry.runtime_data)])


class ProssimaSessione(CoordinatorEntity[F1Coordinator], SensorEntity):
    """Data e ora di inizio della prossima sessione non ancora cominciata."""

    _attr_has_entity_name = True
    _attr_translation_key = "prossima_sessione"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator: F1Coordinator) -> None:
        super().__init__(coordinator)
        self.entity_id = "sensor.f1_prossima_sessione"
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_prossima_sessione"
        self._attr_device_info = coordinator.device_info

    @property
    def native_value(self) -> datetime | None:
        prossima = self.coordinator.stato_attuale()[1]
        return prossima.inizio if prossima else None

    @property
    def extra_state_attributes(self) -> dict[str, str] | None:
        prossima = self.coordinator.stato_attuale()[1]
        return prossima.attributi() if prossima else None
