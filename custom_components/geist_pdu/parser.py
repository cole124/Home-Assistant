"""Parse the Geist /api/dev JSON into flat structures.

Kept free of Home Assistant imports so it can be tested on its own.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Reading:
    """One measurement (power, energy, ...) on an outlet or entity."""

    type: str
    value: float | None
    units: str


@dataclass
class Outlet:
    key: str  # index in the API, e.g. "0"
    name: str  # hardware name, e.g. "Outlet 1"
    label: str  # user label, e.g. "Deep Freeze"
    is_on: bool | None
    readings: dict[str, Reading] = field(default_factory=dict)


@dataclass
class Entity:
    """A non-outlet entity on a device: a phase, circuit (breaker), total or sensor."""

    key: str  # e.g. "phase0", "breaker1", "total0", "0"
    label: str
    readings: dict[str, Reading] = field(default_factory=dict)


@dataclass
class Device:
    device_id: str
    label: str
    type: str
    available: bool
    outlets: dict[str, Outlet] = field(default_factory=dict)
    entities: dict[str, Entity] = field(default_factory=dict)


def _to_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_readings(raw: dict[str, Any] | None) -> dict[str, Reading]:
    readings: dict[str, Reading] = {}
    for item in (raw or {}).values():
        if not isinstance(item, dict) or "type" not in item:
            continue
        value = None if item.get("state") == "unavailable" else _to_float(item.get("value"))
        readings[item["type"]] = Reading(
            type=item["type"], value=value, units=item.get("units", "")
        )
    return readings


def parse_devices(payload: dict[str, Any]) -> dict[str, Device]:
    """Turn the full /api/dev response into Device objects keyed by device id."""
    data = payload.get("data", payload)
    devices: dict[str, Device] = {}
    for device_id, raw in data.items():
        if not isinstance(raw, dict):
            continue
        device = Device(
            device_id=device_id,
            label=raw.get("label") or raw.get("name") or device_id,
            type=raw.get("type", ""),
            available=raw.get("state") != "unavailable",
        )
        for key, out in (raw.get("outlet") or {}).items():
            state = out.get("state")
            device.outlets[key] = Outlet(
                key=key,
                name=out.get("name") or f"Outlet {int(key) + 1}",
                label=out.get("label") or out.get("name") or f"Outlet {int(key) + 1}",
                is_on=None if state not in ("on", "off") else state == "on",
                readings=_parse_readings(out.get("measurement")),
            )
        for key, ent in (raw.get("entity") or {}).items():
            device.entities[key] = Entity(
                key=key,
                label=ent.get("label") or ent.get("name") or key,
                readings=_parse_readings(ent.get("measurement")),
            )
        devices[device_id] = device
    return devices


def find_pdu_id(payload: dict[str, Any]) -> str | None:
    """Return the id of the first device that has outlets (the PDU itself)."""
    for device_id, device in parse_devices(payload).items():
        if device.outlets:
            return device_id
    return None
