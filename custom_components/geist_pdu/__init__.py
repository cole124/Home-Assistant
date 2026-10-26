"""Geist rPDU integration: one Home Assistant device per outlet."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import GeistClient
from .coordinator import GeistCoordinator

PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR]

type GeistConfigEntry = ConfigEntry[GeistCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: GeistConfigEntry) -> bool:
    client = GeistClient(async_get_clientsession(hass), entry.data[CONF_HOST])
    coordinator = GeistCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: GeistConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
