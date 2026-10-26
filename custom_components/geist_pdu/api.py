"""Minimal client for the Geist rPDU JSON API (read only)."""

from __future__ import annotations

import asyncio
from typing import Any

import aiohttp

from .const import API_PATH


class GeistError(Exception):
    """Raised when the PDU cannot be reached or returns bad data."""


class GeistClient:
    def __init__(self, session: aiohttp.ClientSession, host: str) -> None:
        self._session = session
        host = host.strip().rstrip("/")
        if not host.startswith(("http://", "https://")):
            host = f"http://{host}"
        self._base = host

    async def async_get_data(self) -> dict[str, Any]:
        try:
            async with asyncio.timeout(15):
                resp = await self._session.get(f"{self._base}{API_PATH}")
                resp.raise_for_status()
                payload = await resp.json(content_type=None)
        except (aiohttp.ClientError, TimeoutError, ValueError) as err:
            raise GeistError(f"Error talking to PDU: {err}") from err
        if not isinstance(payload, dict) or "data" not in payload:
            raise GeistError("Unexpected response from PDU")
        return payload
