"""Parser tests using the structure returned by Cole's PDU at /api/dev."""

import importlib.util
import pathlib
import sys

_path = pathlib.Path(__file__).parents[1] / "custom_components/geist_pdu/parser.py"
_spec = importlib.util.spec_from_file_location("geist_parser", _path)
parser = importlib.util.module_from_spec(_spec)
sys.modules["geist_parser"] = parser  # dataclasses need the module registered
_spec.loader.exec_module(parser)


def m(mtype, value, units, state="normal"):
    return {"type": mtype, "value": value, "units": units, "state": state,
            "displayEnabled": False, "datalogEnabled": True,
            "alarm": {"severity": "", "state": "none"}}


PAYLOAD = {
    "data": {
        "DA000000A866ED12": {
            "type": "afht3", "label": "RTAFHD3", "name": "RTAFHD3", "state": "normal",
            "entity": {"0": {"name": "RTAFHD3", "measurement": {
                "0": m("temperature", "23.38", "C"),
                "1": m("humidity", "47", "%"),
                "2": m("dewpoint", "11.43", "C"),
                "3": m("airflow", "30", "")}}},
        },
        "1E000009A0FD9428": {
            "type": "remotetemp", "label": "SRT", "name": "SRT", "state": "unavailable",
            "entity": {"0": {"name": "SRT", "measurement": {
                "0": m("temperature", "", "F", state="unavailable")}}},
        },
        "A86B930C851900C3": {
            "label": "Geist Upgradable rPDU", "name": "Geist Upgradable rPDU",
            "state": "normal", "type": "i03",
            "outlet": {
                "9": {"label": "Deep Freeze", "name": "Outlet 10", "state": "on",
                      "measurement": {
                          "8": m("realPower", "28", "W"),
                          "11": m("energy", "656.724", "kWh"),
                          "4": m("current", "0.38", "A"),
                          "0": m("voltage", "118.6", "Vrms"),
                          "10": m("powerFactor", "62", "%"),
                          "9": m("apparentPower", "45", "VA"),
                          "14": m("currentCrestFactor", "3.07", ""),
                      }},
                "0": {"label": "Outlet 1", "name": "Outlet 1", "state": "off",
                      "measurement": {"8": m("realPower", "0", "W")}},
            },
            "entity": {
                "phase0": {"name": "Phase A", "label": "Phase A", "measurement": {
                    "8": m("realPower", "495", "W"),
                    "11": m("energy", "14236.111", "kWh"),
                    "12": m("balance", "100", "%")}},
                "breaker1": {"name": "Circuit 2", "label": "Circuit 2", "measurement": {
                    "4": m("current", "1.28", "A")}},
                "total0": {"name": "Total", "label": "Total", "measurement": {
                    "8": m("realPower", "495", "W")}},
            },
        },
    }
}


def test_finds_pdu():
    assert parser.find_pdu_id(PAYLOAD) == "A86B930C851900C3"


def test_outlets():
    pdu = parser.parse_devices(PAYLOAD)["A86B930C851900C3"]
    assert pdu.label == "Geist Upgradable rPDU"
    freeze = pdu.outlets["9"]
    assert freeze.label == "Deep Freeze" and freeze.name == "Outlet 10"
    assert freeze.is_on is True
    assert freeze.readings["realPower"].value == 28.0
    assert freeze.readings["energy"].value == 656.724
    assert freeze.readings["voltage"].value == 118.6
    assert set(freeze.readings) == {
        "realPower", "energy", "current", "voltage", "powerFactor",
        "apparentPower", "currentCrestFactor"}
    assert pdu.outlets["0"].is_on is False


def test_entities():
    pdu = parser.parse_devices(PAYLOAD)["A86B930C851900C3"]
    assert pdu.entities["breaker1"].label == "Circuit 2"
    assert pdu.entities["breaker1"].readings["current"].value == 1.28
    assert pdu.entities["phase0"].readings["energy"].value == 14236.111


def test_unavailable_probe():
    probe = parser.parse_devices(PAYLOAD)["1E000009A0FD9428"]
    assert probe.available is False
    assert probe.outlets == {}
    assert probe.entities["0"].readings["temperature"].value is None


def test_bad_values():
    assert parser._to_float("") is None
    assert parser._to_float("abc") is None
    assert parser._to_float("1.5") == 1.5
