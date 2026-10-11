"""Flusso di configurazione di F1 Live Map."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback

from .const import (
    CONF_ANTICIPO,
    CONF_EXTRA,
    DEFAULT_ANTICIPO,
    DEFAULT_EXTRA,
    DOMAIN,
    NOME,
)


class F1ConfigFlow(ConfigFlow, domain=DOMAIN):
    """Un solo passaggio di conferma: non ci sono dati da chiedere."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(title=NOME, data={})
        return self.async_show_form(step_id="user")

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return F1OptionsFlow()


class F1OptionsFlow(OptionsFlow):
    """Margini prima e dopo la sessione."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)
        opzioni = self.config_entry.options
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_ANTICIPO, default=opzioni.get(CONF_ANTICIPO, DEFAULT_ANTICIPO)
                    ): vol.All(vol.Coerce(int), vol.Range(min=0, max=120)),
                    vol.Required(
                        CONF_EXTRA, default=opzioni.get(CONF_EXTRA, DEFAULT_EXTRA)
                    ): vol.All(vol.Coerce(int), vol.Range(min=0, max=240)),
                }
            ),
        )
