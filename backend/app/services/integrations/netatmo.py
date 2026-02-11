"""Netatmo Energy API integration."""
import logging
import random
from datetime import datetime, timedelta
from typing import Optional

from app.services.integrations.base import BaseIntegration

logger = logging.getLogger(__name__)


class NetatmoClient(BaseIntegration):
    """Client for Netatmo Energy API."""

    BASE_URL = "https://api.netatmo.com"

    async def get_thermostats(self, access_token: str) -> list[dict]:
        """Get all thermostats from Netatmo account."""
        response = await self._make_request(
            "GET",
            f"{self.BASE_URL}/api/homestatus",
            headers={"Authorization": f"Bearer {access_token}"},
            _mock_key="homestatus",
        )
        return response.get("body", {}).get("home", {}).get("modules", [])

    async def set_thermpoint(
        self,
        access_token: str,
        device_id: str,
        module_id: str,
        temp: float,
        duration_min: int = 60,
    ) -> bool:
        """Set thermostat temperature setpoint."""
        response = await self._make_request(
            "POST",
            f"{self.BASE_URL}/api/setthermpoint",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "device_id": device_id,
                "module_id": module_id,
                "setpoint_mode": "manual",
                "setpoint_temp": temp,
                "setpoint_endtime": int((datetime.now() + timedelta(minutes=duration_min)).timestamp()),
            },
            _mock_key="setthermpoint",
        )
        return response.get("status") == "ok"

    async def get_home_data(self, access_token: str) -> dict:
        """Get home data including devices and modules."""
        response = await self._make_request(
            "GET",
            f"{self.BASE_URL}/api/homesdata",
            headers={"Authorization": f"Bearer {access_token}"},
            _mock_key="homesdata",
        )
        return response.get("body", {}).get("homes", [{}])[0]

    def _mock_response(self, method: str, url: str, **kwargs) -> dict:
        mock_key = kwargs.pop("_mock_key", "")

        if mock_key == "homestatus":
            return {
                "body": {
                    "home": {
                        "modules": [
                            {
                                "id": "netatmo-therm-001",
                                "type": "NATherm1",
                                "name": "Thermostat Bureau",
                                "setup_date": 1609459200,
                                "room_id": "room-1",
                                "measured_temperature": round(20.5 + random.uniform(-1, 1), 1),
                                "setpoint_temp": 21.0,
                                "setpoint_mode": "schedule",
                                "boiler_status": True,
                            },
                            {
                                "id": "netatmo-therm-002",
                                "type": "NATherm1",
                                "name": "Thermostat Salle de Réunion",
                                "setup_date": 1609459200,
                                "room_id": "room-2",
                                "measured_temperature": round(21.0 + random.uniform(-1, 1), 1),
                                "setpoint_temp": 22.0,
                                "setpoint_mode": "schedule",
                                "boiler_status": False,
                            },
                        ]
                    }
                },
                "status": "ok",
            }

        if mock_key == "setthermpoint":
            logger.info("Mock: Netatmo thermpoint set successfully")
            return {"status": "ok"}

        if mock_key == "homesdata":
            return {
                "body": {
                    "homes": [
                        {
                            "id": "home-001",
                            "name": "Bureau Principal",
                            "rooms": [
                                {"id": "room-1", "name": "Bureau Open Space", "type": "custom"},
                                {"id": "room-2", "name": "Salle de Réunion", "type": "custom"},
                            ],
                            "modules": [
                                {"id": "netatmo-therm-001", "type": "NATherm1", "name": "Thermostat Bureau"},
                                {"id": "netatmo-therm-002", "type": "NATherm1", "name": "Thermostat Réunion"},
                            ],
                        }
                    ]
                },
                "status": "ok",
            }

        return {"status": "ok"}
