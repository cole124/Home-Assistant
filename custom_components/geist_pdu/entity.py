"""Shared entity base and device info for the Geist rPDU integration."""

from __future__ import annotations

from homeassistant.const import CONF_HOST
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import GeistCoordinator
from .parser import Device, Entity, Outlet


def hub_device_info(coordinator: GeistCoordinator, device: Device, pdu_id: str) -> DeviceInfo:
    """Device info for the PDU itself or an attached sensor (e.g. a remote temp probe)."""
    info = DeviceInfo(
        identifiers={(DOMAIN, device.device_id)},
        name=device.label,
        manufacturer=MANUFACTURER,
        model="rPDU" if device.device_id == pdu_id else device.type or None,
        serial_number=device.device_id,
    )
    if device.device_id == pdu_id:
        host = coordinator.config_entry.data[CONF_HOST]
        info["configuration_url"] = host if host.startswith("http") else f"http://{host}"
    else:
        info["via_device"] = (DOMAIN, pdu_id)
    return info


def outlet_device_info(device: Device, outlet: Outlet) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, f"{device.device_id}_outlet{outlet.key}")},
        name=outlet.label,
        manufacturer=MANUFACTURER,
        model=f"{device.label} {outlet.name}",
        via_device=(DOMAIN, device.device_id),
    )


class GeistEntity(CoordinatorEntity[GeistCoordinator]):
    """Base entity that looks itself up in the latest coordinator data."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: GeistCoordinator,
        device_id: str,
        outlet_key: str | None = None,
        entity_key: str | None = None,
    ) -> None:
        super().__init__(coordinator)
        self._device_id = device_id
        self._outlet_key = outlet_key
        self._entity_key = entity_key

    @property
    def _device(self) -> Device | None:
        return (self.coordinator.data or {}).get(self._device_id)

    @property
    def _outlet(self) -> Outlet | None:
        device = self._device
        if device is None or self._outlet_key is None:
            return None
        return device.outlets.get(self._outlet_key)

    @property
    def _entity(self) -> Entity | None:
        device = self._device
        if device is None or self._entity_key is None:
            return None
        return device.entities.get(self._entity_key)

    @property
    def available(self) -> bool:
        device = self._device
        return super().available and device is not None and device.available
