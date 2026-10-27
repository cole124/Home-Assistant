"""Sensors for each outlet, circuit, phase and attached probe."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    UnitOfApparentPower,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import GeistConfigEntry
from .coordinator import GeistCoordinator
from .entity import GeistEntity, hub_device_info, outlet_device_info
from .parser import Reading


@dataclass(frozen=True, kw_only=True)
class GeistSensorDescription(SensorEntityDescription):
    """Maps a Geist measurement type to a Home Assistant sensor."""


SENSORS: dict[str, GeistSensorDescription] = {
    "realPower": GeistSensorDescription(
        key="realPower",
        name="Power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
    ),
    "energy": GeistSensorDescription(
        key="energy",
        name="Energy",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=2,
    ),
    "current": GeistSensorDescription(
        key="current",
        name="Current",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        suggested_display_precision=2,
    ),
    "voltage": GeistSensorDescription(
        key="voltage",
        name="Voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        suggested_display_precision=1,
    ),
    "powerFactor": GeistSensorDescription(
        key="powerFactor",
        name="Power factor",
        device_class=SensorDeviceClass.POWER_FACTOR,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
    ),
    "apparentPower": GeistSensorDescription(
        key="apparentPower",
        name="Apparent power",
        device_class=SensorDeviceClass.APPARENT_POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfApparentPower.VOLT_AMPERE,
        entity_registry_enabled_default=False,
    ),
    "currentCrestFactor": GeistSensorDescription(
        key="currentCrestFactor",
        name="Current crest factor",
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    "balance": GeistSensorDescription(
        key="balance",
        name="Balance",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        entity_registry_enabled_default=False,
    ),
    "temperature": GeistSensorDescription(
        key="temperature",
        name="Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    "dewpoint": GeistSensorDescription(
        key="dewpoint",
        name="Dew point",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    "airflow": GeistSensorDescription(
        key="airflow",
        name="Airflow",
        icon="mdi:weather-windy",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "humidity": GeistSensorDescription(
        key="humidity",
        name="Humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
    ),
}

TEMP_UNITS = {"F": UnitOfTemperature.FAHRENHEIT, "C": UnitOfTemperature.CELSIUS}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: GeistConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    devices = coordinator.data
    pdu_id = entry.unique_id or next(iter(devices))
    entities: list[GeistSensor] = []

    for device in devices.values():
        has_phase = any(k.startswith("phase") for k in device.entities)
        for outlet in device.outlets.values():
            for mtype in outlet.readings:
                if mtype in SENSORS:
                    entities.append(
                        GeistSensor(coordinator, device.device_id, mtype, outlet_key=outlet.key)
                    )
        for ent in device.entities.values():
            for mtype in ent.readings:
                if mtype in SENSORS:
                    entities.append(
                        GeistSensor(
                            coordinator,
                            device.device_id,
                            mtype,
                            entity_key=ent.key,
                            pdu_id=pdu_id,
                            # On a single-phase PDU the totals repeat the phase readings.
                            disabled=ent.key.startswith("total") and has_phase,
                        )
                    )

    async_add_entities(entities)


class GeistSensor(GeistEntity, SensorEntity):
    entity_description: GeistSensorDescription

    def __init__(
        self,
        coordinator: GeistCoordinator,
        device_id: str,
        mtype: str,
        outlet_key: str | None = None,
        entity_key: str | None = None,
        pdu_id: str | None = None,
        disabled: bool = False,
    ) -> None:
        super().__init__(coordinator, device_id, outlet_key, entity_key)
        self._mtype = mtype
        self.entity_description = SENSORS[mtype]
        device = coordinator.data[device_id]
        pdu_id = pdu_id or device_id

        if outlet_key is not None:
            outlet = device.outlets[outlet_key]
            self._attr_unique_id = f"{device_id}_outlet{outlet_key}_{mtype}"
            self._attr_device_info = outlet_device_info(device, outlet)
        else:
            ent = device.entities[entity_key]
            self._attr_unique_id = f"{device_id}_{entity_key}_{mtype}"
            self._attr_device_info = hub_device_info(coordinator, device, pdu_id)
            # On the PDU device, prefix with the phase/circuit name ("Circuit 1 Current").
            # A probe's single entity shares its device's name, so no prefix there.
            if ent.label != device.label:
                self._attr_name = f"{ent.label} {self.entity_description.name}"
            if disabled:
                self._attr_entity_registry_enabled_default = False

        if mtype in ("temperature", "dewpoint"):
            reading = self._reading
            self._attr_native_unit_of_measurement = TEMP_UNITS.get(
                (reading.units if reading else "F").upper(), UnitOfTemperature.FAHRENHEIT
            )

    @property
    def _reading(self) -> Reading | None:
        source = self._outlet if self._outlet_key is not None else self._entity
        return source.readings.get(self._mtype) if source else None

    @property
    def available(self) -> bool:
        reading = self._reading
        return super().available and reading is not None and reading.value is not None

    @property
    def native_value(self) -> float | None:
        reading = self._reading
        return reading.value if reading else None
