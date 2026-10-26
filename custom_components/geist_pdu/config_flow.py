"""Config flow: ask for the PDU's address and confirm it answers."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import GeistClient, GeistError
from .const import DOMAIN
from .parser import find_pdu_id, parse_devices


class GeistConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            client = GeistClient(async_get_clientsession(self.hass), host)
            try:
                payload = await client.async_get_data()
            except GeistError:
                errors["base"] = "cannot_connect"
            else:
                pdu_id = find_pdu_id(payload)
                if pdu_id is None:
                    errors["base"] = "no_outlets"
                else:
                    await self.async_set_unique_id(pdu_id)
                    self._abort_if_unique_id_configured(updates={CONF_HOST: host})
                    title = parse_devices(payload)[pdu_id].label
                    return self.async_create_entry(title=title, data={CONF_HOST: host})

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_HOST): str}),
            errors=errors,
        )
