"""Load the integration in a real Home Assistant instance with a mocked PDU."""

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.const import CONF_HOST
from homeassistant.helpers import device_registry as dr, entity_registry as er

from custom_components.geist_pdu.const import DOMAIN

from .test_parser import PAYLOAD

URL = "http://192.168.1.148/api/dev"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield


async def test_setup_creates_devices(hass, aioclient_mock):
    aioclient_mock.get(URL, json=PAYLOAD)
    entry = MockConfigEntry(
        domain=DOMAIN, data={CONF_HOST: "192.168.1.148"}, unique_id="A86B930C851900C3"
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    devreg = dr.async_get(hass)
    freeze = devreg.async_get_device(identifiers={(DOMAIN, "A86B930C851900C3_outlet9")})
    assert freeze is not None and freeze.name == "Deep Freeze"
    pdu = devreg.async_get_device(identifiers={(DOMAIN, "A86B930C851900C3")})
    assert freeze.via_device_id == pdu.id

    power = hass.states.get("sensor.deep_freeze_power")
    assert power is not None and float(power.state) == 28.0
    assert power.attributes["unit_of_measurement"] == "W"
    energy = hass.states.get("sensor.deep_freeze_energy")
    assert float(energy.state) == 656.724
    assert energy.attributes["state_class"] == "total_increasing"
    assert hass.states.get("binary_sensor.deep_freeze_outlet").state == "on"
    assert hass.states.get("binary_sensor.outlet_1_outlet").state == "off"

    circuit = hass.states.get("sensor.geist_upgradable_rpdu_circuit_2_current")
    assert circuit is not None and float(circuit.state) == 1.28

    entreg = er.async_get(hass)
    # Disabled by default: apparent power, and the total that repeats the phase.
    assert entreg.async_get("sensor.deep_freeze_apparent_power").disabled_by
    assert entreg.async_get("sensor.geist_upgradable_rpdu_total_power").disabled_by

    # The unavailable probe shows as unavailable, not as an error.
    assert hass.states.get("sensor.srt_temperature").state == "unavailable"


async def test_config_flow(hass, aioclient_mock):
    aioclient_mock.get(URL, json=PAYLOAD)
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "192.168.1.148"}
    )
    assert result["type"] == "create_entry"
    assert result["title"] == "Geist Upgradable rPDU"
    assert result["result"].unique_id == "A86B930C851900C3"
