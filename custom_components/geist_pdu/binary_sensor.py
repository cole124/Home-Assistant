"""On/off state of each outlet (read only)."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import GeistConfigEntry
from .coordinator import GeistCoordinator
from .entity import GeistEntity, outlet_device_info


async def async_setup_entry(
    hass: HomeAssistant,
    entry: GeistConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        GeistOutletState(coordinator, device.device_id, outlet.key)
        for device in coordinator.data.values()
        for outlet in device.outlets.values()
    )


class GeistOutletState(GeistEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.POWER
    _attr_name = "Outlet"

    def __init__(self, coordinator: GeistCoordinator, device_id: str, outlet_key: str) -> None:
        super().__init__(coordinator, device_id, outlet_key=outlet_key)
        device = coordinator.data[device_id]
        outlet = device.outlets[outlet_key]
        self._attr_unique_id = f"{device_id}_outlet{outlet_key}_state"
        self._attr_device_info = outlet_device_info(device, outlet)

    @property
    def available(self) -> bool:
        outlet = self._outlet
        return super().available and outlet is not None and outlet.is_on is not None

    @property
    def is_on(self) -> bool | None:
        outlet = self._outlet
        return outlet.is_on if outlet else None
