# Geist rPDU for Home Assistant

Monitors a Vertiv Geist rack PDU over its local JSON API (`/api/dev`) and
creates one Home Assistant device per outlet. Read only: it never switches
outlets.

## What you get

- **A device per outlet**, named from the outlet's label on the PDU, with:
  power (W), energy (kWh), current (A), voltage (V), power factor (%), and an
  on/off "Outlet" sensor. Apparent power and crest factor are created disabled.
- **The PDU device** with phase readings and per-circuit current.
- **Attached probes** (such as remote temperature sensors) as their own devices.

Outlet energy sensors work on the Energy dashboard as individual devices.

Data is polled every 30 seconds. No login is needed.

## Install (HACS)

1. HACS → three-dot menu → **Custom repositories**.
2. Add this repository's URL with type **Integration**.
3. Install **Geist rPDU** and restart Home Assistant.
4. Settings → Devices & services → **Add integration** → **Geist rPDU**, then
   enter the PDU's IP address.

## Notes

- Renaming an outlet on the PDU doesn't rename its existing Home Assistant
  device; rename it in Home Assistant.
- Tested against a Geist Upgradable rPDU (`type: i03`) with 12 outlets on one phase.
