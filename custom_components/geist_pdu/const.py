"""Constants for the Geist rPDU integration."""

from datetime import timedelta

DOMAIN = "geist_pdu"
MANUFACTURER = "Vertiv Geist"
DEFAULT_SCAN_INTERVAL = timedelta(seconds=30)
API_PATH = "/api/dev"
