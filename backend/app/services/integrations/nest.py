"""
Google Nest (Smart Device Management) integration client.

Supports thermostat discovery, state retrieval, and remote temperature / mode
changes via the SDM API.  Mock mode returns realistic office thermostat data
with French room names.

Reference: https://developers.google.com/nest/device-access/api
"""

from __future__ import annotations

import random
from typing import Any

import structlog

from app.config import settings
from app.services.integrations.base import BaseIntegration

logger: structlog.stdlib.BoundLogger = structlog.get_logger(__name__)

# ── SDM endpoints ────────────────────────────────────────────────────────
_SDM_BASE = "https://smartdevicemanagement.googleapis.com/v1"


def _enterprise_url(project_id: str) -> str:
    return f"{_SDM_BASE}/enterprises/{project_id}"


class NestClient(BaseIntegration):
    """Client for the Google Smart Device Management (Nest) API."""

    SERVICE_NAME: str = "nest"

    # ── Device discovery ─────────────────────────────────────────────────

    async def discover_devices(
        self,
        access_token: str,
        project_id: str,
    ) -> list[dict]:
        """List all thermostats visible to the service account.

        Returns
        -------
        list[dict]
            Each entry contains ``device_id``, ``name``, ``type``,
            and ``room``.
        """
        url = f"{_enterprise_url(project_id)}/devices"
        raw = await self._make_request(
            "GET",
            url,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        return self._parse_devices(raw)

    # ── Current state ────────────────────────────────────────────────────

    async def get_current_state(
        self,
        access_token: str,
        project_id: str,
        device_id: str,
    ) -> dict:
        """Get the current thermostat state (temperature, humidity, mode).

        Returns
        -------
        dict
            Keys: ``device_id``, ``ambient_temp_celsius``,
            ``target_temp_celsius``, ``humidity_pct``, ``hvac_mode``,
            ``hvac_status``, ``connectivity``.
        """
        url = f"{_enterprise_url(project_id)}/devices/{device_id}"
        raw = await self._make_request(
            "GET",
            url,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        return self._parse_state(raw, device_id)

    # ── Set temperature ──────────────────────────────────────────────────

    async def set_temperature(
        self,
        access_token: str,
        project_id: str,
        device_id: str,
        temp: float,
    ) -> bool:
        """Set the target temperature on a thermostat.

        Parameters
        ----------
        temp:
            Desired temperature in degrees Celsius.

        Returns
        -------
        bool
            ``True`` if the command was accepted.
        """
        url = f"{_enterprise_url(project_id)}/devices/{device_id}:executeCommand"
        await self._make_request(
            "POST",
            url,
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "command": "sdm.devices.commands.ThermostatTemperatureSetpoint.SetHeat",
                "params": {"heatCelsius": temp},
            },
        )
        logger.info(
            "nest.set_temperature",
            device_id=device_id,
            temp_celsius=temp,
        )
        return True

    # ── Set mode ─────────────────────────────────────────────────────────

    async def set_mode(
        self,
        access_token: str,
        project_id: str,
        device_id: str,
        mode: str,
    ) -> bool:
        """Set the HVAC mode (HEAT, COOL, HEATCOOL, OFF).

        Returns
        -------
        bool
            ``True`` if the command was accepted.
        """
        url = f"{_enterprise_url(project_id)}/devices/{device_id}:executeCommand"
        await self._make_request(
            "POST",
            url,
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "command": "sdm.devices.commands.ThermostatMode.SetMode",
                "params": {"mode": mode.upper()},
            },
        )
        logger.info(
            "nest.set_mode",
            device_id=device_id,
            mode=mode,
        )
        return True

    # ── Response parsing ─────────────────────────────────────────────────

    @staticmethod
    def _parse_devices(raw: dict | list) -> list[dict]:
        if isinstance(raw, list):
            return raw
        devices = raw.get("devices", [])
        result: list[dict] = []
        for d in devices:
            name_full: str = d.get("name", "")
            device_id = name_full.rsplit("/", 1)[-1] if "/" in name_full else name_full
            traits = d.get("traits", {})
            room = (
                traits
                .get("sdm.structures.traits.Info", {})
                .get("customName", "")
            ) or d.get("parentRelations", [{}])[0].get("displayName", "Unknown")
            result.append(
                {
                    "device_id": device_id,
                    "name": name_full,
                    "type": d.get("type", "sdm.devices.types.THERMOSTAT"),
                    "room": room,
                }
            )
        return result

    @staticmethod
    def _parse_state(raw: dict, device_id: str) -> dict:
        if "ambient_temp_celsius" in raw:
            return raw  # already normalised (mock)
        traits = raw.get("traits", {})
        ambient = (
            traits
            .get("sdm.devices.traits.Temperature", {})
            .get("ambientTemperatureCelsius", 0.0)
        )
        humidity = (
            traits
            .get("sdm.devices.traits.Humidity", {})
            .get("ambientHumidityPercent", 0)
        )
        mode = (
            traits
            .get("sdm.devices.traits.ThermostatMode", {})
            .get("mode", "OFF")
        )
        hvac_status = (
            traits
            .get("sdm.devices.traits.ThermostatHvac", {})
            .get("status", "OFF")
        )
        setpoint = (
            traits
            .get("sdm.devices.traits.ThermostatTemperatureSetpoint", {})
            .get("heatCelsius", 0.0)
        )
        connectivity = (
            traits
            .get("sdm.devices.traits.Connectivity", {})
            .get("status", "ONLINE")
        )
        return {
            "device_id": device_id,
            "ambient_temp_celsius": ambient,
            "target_temp_celsius": setpoint,
            "humidity_pct": humidity,
            "hvac_mode": mode,
            "hvac_status": hvac_status,
            "connectivity": connectivity,
        }

    # ── Mock implementation ──────────────────────────────────────────────

    def _mock_response(self, method: str, url: str, **kwargs: Any) -> dict | list:
        if method == "POST" and "executeCommand" in url:
            return self._mock_command()
        if "/devices/" in url and method == "GET" and not url.rstrip("/").endswith("/devices"):
            # Single-device state request
            device_id = url.rstrip("/").rsplit("/", 1)[-1]
            return self._mock_state(device_id)
        if url.rstrip("/").endswith("/devices"):
            return self._mock_discover()
        return {}

    # -- mock helpers -----------------------------------------------------

    _FAKE_DEVICES = [
        {
            "device_id": "nest-thermo-001",
            "name": "enterprises/mock-project/devices/nest-thermo-001",
            "type": "sdm.devices.types.THERMOSTAT",
            "room": "Bureau Principal",
        },
        {
            "device_id": "nest-thermo-002",
            "name": "enterprises/mock-project/devices/nest-thermo-002",
            "type": "sdm.devices.types.THERMOSTAT",
            "room": "Salle R\u00e9union",
        },
        {
            "device_id": "nest-thermo-003",
            "name": "enterprises/mock-project/devices/nest-thermo-003",
            "type": "sdm.devices.types.THERMOSTAT",
            "room": "Accueil",
        },
    ]

    def _mock_discover(self) -> list[dict]:
        return list(self._FAKE_DEVICES)

    @staticmethod
    def _mock_state(device_id: str) -> dict:
        rng = random.Random(hash(device_id))
        return {
            "device_id": device_id,
            "ambient_temp_celsius": round(rng.uniform(20.0, 22.0), 1),
            "target_temp_celsius": round(rng.uniform(20.5, 22.0), 1),
            "humidity_pct": rng.randint(40, 60),
            "hvac_mode": "HEAT",
            "hvac_status": rng.choice(["HEATING", "OFF"]),
            "connectivity": "ONLINE",
        }

    @staticmethod
    def _mock_command() -> dict:
        return {"results": {}}
