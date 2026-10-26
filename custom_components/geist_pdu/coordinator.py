"""Polling coordinator for the Geist rPDU."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import GeistClient, GeistError
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN
from .parser import Device, parse_devices

_LOGGER = logging.getLogger(__name__)


class GeistCoordinator(DataUpdateCoordinator[dict[str, Device]]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, client: GeistClient) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=DEFAULT_SCAN_INTERVAL,
        )
        self.client = client

    async def _async_update_data(self) -> dict[str, Device]:
        try:
            payload = await self.client.async_get_data()
        except GeistError as err:
            raise UpdateFailed(str(err)) from err
        return parse_devices(payload)
