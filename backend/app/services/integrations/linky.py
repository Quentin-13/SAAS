"""
Enedis Linky (Data Connect) integration client.

Handles OAuth2 token exchange and consumption data retrieval from the
Enedis Data Connect API.  In mock mode, returns 48 hours of realistic
household / small-business consumption data.

Reference: https://datahub-enedis.fr/data-connect/documentation/
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone
from typing import Any

import structlog

from app.config import settings
from app.services.integrations.base import BaseIntegration

logger: structlog.stdlib.BoundLogger = structlog.get_logger(__name__)

# ── Enedis endpoints ─────────────────────────────────────────────────────
_AUTH_BASE = "https://gw.hml.api.enedis.fr"
_TOKEN_PATH = "/v1/oauth2/token"
_DATA_BASE = settings.ENEDIS_API_BASE_URL  # ext.hml.api.enedis.fr
_CONSUMPTION_PATH = "/metering_data_clc/v5/consumption_load_curve"


class LinkyClient(BaseIntegration):
    """Client for the Enedis Data Connect API (Linky smart meters)."""

    SERVICE_NAME: str = "linky"

    # ── OAuth2 token exchange ────────────────────────────────────────────

    async def authorize(self, authorization_code: str) -> dict:
        """Exchange an OAuth2 authorization code for access/refresh tokens.

        Parameters
        ----------
        authorization_code:
            The code returned by the Enedis consent redirect.

        Returns
        -------
        dict
            Contains ``access_token``, ``refresh_token``,
            ``token_type``, and ``expires_in``.
        """
        url = f"{_AUTH_BASE}{_TOKEN_PATH}"
        return await self._make_request(
            "POST",
            url,
            data={
                "grant_type": "authorization_code",
                "code": authorization_code,
                "client_id": settings.ENEDIS_API_KEY,
                "redirect_uri": f"{settings.ALLOWED_ORIGINS[0]}/callback/enedis",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

    # ── Consumption data ─────────────────────────────────────────────────

    async def get_consumption(
        self,
        access_token: str,
        usage_point_id: str,
        start: str,
        end: str,
    ) -> list[dict]:
        """Retrieve the consumption load curve for a usage point.

        Parameters
        ----------
        access_token:
            Bearer token from ``authorize``.
        usage_point_id:
            The Enedis PRM / usage-point identifier.
        start:
            Start date in ``YYYY-MM-DD`` format.
        end:
            End date in ``YYYY-MM-DD`` format.

        Returns
        -------
        list[dict]
            Each entry has ``time`` (ISO-8601), ``power_kw`` (float),
            and ``energy_kwh`` (float).
        """
        url = f"{_DATA_BASE}{_CONSUMPTION_PATH}"
        raw = await self._make_request(
            "GET",
            url,
            params={
                "usage_point_id": usage_point_id,
                "start": start,
                "end": end,
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )

        # Normalise the Enedis response into our standard shape.
        return self._parse_consumption(raw)

    # ── Response parsing ─────────────────────────────────────────────────

    @staticmethod
    def _parse_consumption(raw: dict | list) -> list[dict]:
        """Normalise Enedis or mock payload into ``[{time, power_kw, energy_kwh}]``."""
        # If the mock/real response is already a list of dicts, return as-is.
        if isinstance(raw, list):
            return raw

        # Enedis wraps interval data under meter_reading -> interval_reading.
        try:
            readings = (
                raw.get("meter_reading", {})
                .get("interval_reading", [])
            )
        except AttributeError:
            logger.warning("linky.parse_unexpected_shape", raw_type=type(raw).__name__)
            return []

        result: list[dict] = []
        for r in readings:
            power_w = float(r.get("value", 0))
            result.append(
                {
                    "time": r.get("date", ""),
                    "power_kw": round(power_w / 1000.0, 3),
                    "energy_kwh": round(power_w / 1000.0 * 0.5, 3),  # 30-min slot
                }
            )
        return result

    # ── Mock implementation ──────────────────────────────────────────────

    def _mock_response(self, method: str, url: str, **kwargs: Any) -> dict | list:
        """Return realistic fake data depending on the endpoint called."""
        if _TOKEN_PATH in url:
            return self._mock_authorize()
        if _CONSUMPTION_PATH in url or "consumption" in url:
            return self._mock_consumption(kwargs.get("params", {}))
        return {}

    # -- mock helpers -----------------------------------------------------

    @staticmethod
    def _mock_authorize() -> dict:
        return {
            "access_token": "mock-enedis-access-token-" + "a1b2c3d4e5f6",
            "refresh_token": "mock-enedis-refresh-token-" + "f6e5d4c3b2a1",
            "token_type": "Bearer",
            "expires_in": 12600,
            "scope": "/v3/metering_data/consumption_load_curve.GET",
        }

    @staticmethod
    def _mock_consumption(params: dict) -> list[dict]:
        """Generate 48 hours of half-hourly consumption data.

        Pattern
        -------
        - Nights (0h-7h): 1-2 kW (standby / fridge / server room)
        - Business hours (8h-19h weekdays): 4-8 kW (HVAC, lighting, equipment)
        - Evenings (19h-23h): 2-4 kW
        - Weekends: roughly 60 % of weekday daytime
        """
        start_str = params.get("start", datetime.now(tz=timezone.utc).strftime("%Y-%m-%d"))
        try:
            start_dt = datetime.strptime(start_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            start_dt = datetime.now(tz=timezone.utc).replace(
                hour=0, minute=0, second=0, microsecond=0,
            )

        points: list[dict] = []
        rng = random.Random(42)  # deterministic for reproducibility in tests

        for slot in range(96):  # 48h * 2 slots/h
            ts = start_dt + timedelta(minutes=30 * slot)
            hour = ts.hour
            is_weekend = ts.weekday() >= 5

            if 0 <= hour < 7:
                base = rng.uniform(1.0, 2.0)
            elif 8 <= hour < 19:
                base = rng.uniform(4.0, 8.0)
                if is_weekend:
                    base *= 0.6
            elif 19 <= hour < 23:
                base = rng.uniform(2.0, 4.0)
            else:  # 7-8h ramp-up, 23h wind-down
                base = rng.uniform(2.0, 3.5)

            power_kw = round(base, 2)
            energy_kwh = round(power_kw * 0.5, 3)  # 30-min slot
            points.append(
                {
                    "time": ts.isoformat(),
                    "power_kw": power_kw,
                    "energy_kwh": energy_kwh,
                }
            )

        return points
