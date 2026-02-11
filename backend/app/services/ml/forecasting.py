"""Energy forecasting service using Prophet (with fallback to simple heuristics).

Provides 48-hour energy consumption predictions based on historical data,
weather forecasts, and occupancy patterns.
"""

from __future__ import annotations

import logging
import math
from datetime import datetime, timedelta, timezone
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Cost constant (€/kWh) – French regulated tariff reference
# ---------------------------------------------------------------------------
COST_EUR_PER_KWH = 0.2016

# ---------------------------------------------------------------------------
# Try to import Prophet; fall back gracefully if not installed
# ---------------------------------------------------------------------------
_PROPHET_AVAILABLE = False
try:
    from prophet import Prophet  # type: ignore[import-untyped]

    _PROPHET_AVAILABLE = True
except ImportError:
    Prophet = None  # type: ignore[assignment,misc]
    logger.info(
        "Prophet is not installed – forecasting will use the simple fallback model. "
        "Install with: pip install prophet"
    )


# ═══════════════════════════════════════════════════════════════════════════
# Hour-of-day multipliers for the fallback model
# ═══════════════════════════════════════════════════════════════════════════
_HOUR_MULTIPLIERS: dict[int, float] = {
    0: 0.40, 1: 0.35, 2: 0.30, 3: 0.30, 4: 0.30, 5: 0.35,
    6: 0.55, 7: 0.75, 8: 0.95, 9: 1.10, 10: 1.15, 11: 1.10,
    12: 0.90, 13: 0.95, 14: 1.10, 15: 1.10, 16: 1.05, 17: 1.00,
    18: 0.85, 19: 0.70, 20: 0.55, 21: 0.50, 22: 0.45, 23: 0.42,
}

_WEEKEND_FACTOR = 0.60  # weekends use ~60 % of weekday energy


class EnergyForecaster:
    """Forecast energy consumption for a given site.

    When Prophet is available the forecaster trains a full additive model with
    temperature and occupancy regressors.  Otherwise it falls back to a simple
    average-based model with hour-of-day and weekday/weekend adjustments.
    """

    def __init__(self, site_id: str) -> None:
        self.site_id = site_id
        self.model: Any | None = None
        self._fallback_avg_kwh: float | None = None
        self._is_prophet_model = False
        logger.info("EnergyForecaster initialised for site %s", site_id)

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------

    def train(self, historical_data: list[dict]) -> None:
        """Train the forecasting model on historical energy readings.

        Parameters
        ----------
        historical_data:
            List of dicts, each containing at minimum:
            ``datetime`` (ISO-8601 str or datetime), ``energy_kwh`` (float).
            Optionally: ``outdoor_temp`` (float), ``is_occupied`` (bool).
        """
        if not historical_data:
            raise ValueError("historical_data must be a non-empty list")

        df = self._prepare_training_data(historical_data)
        logger.info(
            "Training forecaster for site %s on %d data points",
            self.site_id,
            len(df),
        )

        if _PROPHET_AVAILABLE:
            self._train_prophet(df)
        else:
            self._train_fallback(df)

    def _train_prophet(self, df: pd.DataFrame) -> None:
        """Train a Prophet model with temperature and occupancy regressors."""
        model = Prophet(
            daily_seasonality=True,
            weekly_seasonality=True,
            yearly_seasonality=False,
        )
        model.add_regressor("outdoor_temp")
        model.add_regressor("is_occupied")
        model.fit(df)
        self.model = model
        self._is_prophet_model = True
        logger.info("Prophet model trained successfully for site %s", self.site_id)

    def _train_fallback(self, df: pd.DataFrame) -> None:
        """Compute a simple hourly-average baseline as a fallback model."""
        self._fallback_avg_kwh = float(df["y"].mean())
        self._is_prophet_model = False
        self.model = "fallback"
        logger.info(
            "Fallback model trained for site %s – mean kWh=%.2f",
            self.site_id,
            self._fallback_avg_kwh,
        )

    # ------------------------------------------------------------------
    # Prediction
    # ------------------------------------------------------------------

    def predict_next_48h(self, weather_forecast: list[dict]) -> list[dict]:
        """Predict energy consumption for the next 48 hours.

        Parameters
        ----------
        weather_forecast:
            List of dicts with ``datetime`` (ISO-8601 or datetime),
            ``outdoor_temp`` (float), and ``is_occupied`` (bool).

        Returns
        -------
        list[dict]
            Each entry contains *forecast_date*, *predicted_kwh*,
            *predicted_cost_eur*, *confidence_lower*, *confidence_upper*,
            and *horizon_hours*.
        """
        if self.model is None:
            raise RuntimeError("Model has not been trained yet – call train() first")

        if self._is_prophet_model:
            return self._predict_prophet(weather_forecast)
        return self._predict_fallback(weather_forecast)

    def _predict_prophet(self, weather_forecast: list[dict]) -> list[dict]:
        """Generate predictions using the trained Prophet model."""
        now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
        future = self.model.make_future_dataframe(periods=48, freq="h", include_history=False)

        # Build a lookup for regressor values keyed by rounded hour
        weather_lookup: dict[str, dict] = {}
        for entry in weather_forecast:
            dt = _parse_datetime(entry["datetime"])
            key = dt.strftime("%Y-%m-%d %H:00:00")
            weather_lookup[key] = entry

        temps: list[float] = []
        occupancies: list[float] = []
        for ds_val in future["ds"]:
            key = ds_val.strftime("%Y-%m-%d %H:00:00")
            if key in weather_lookup:
                temps.append(float(weather_lookup[key].get("outdoor_temp", 15.0)))
                occupancies.append(1.0 if weather_lookup[key].get("is_occupied", False) else 0.0)
            else:
                temps.append(15.0)
                occupancies.append(0.0)

        future["outdoor_temp"] = temps
        future["is_occupied"] = occupancies

        forecast = self.model.predict(future)

        results: list[dict] = []
        for idx, row in forecast.iterrows():
            horizon = max(1, int((row["ds"].to_pydatetime() - now.replace(tzinfo=None)).total_seconds() / 3600))
            predicted_kwh = max(0.0, float(row["yhat"]))
            results.append(
                {
                    "forecast_date": row["ds"].isoformat(),
                    "predicted_kwh": round(predicted_kwh, 2),
                    "predicted_cost_eur": round(predicted_kwh * COST_EUR_PER_KWH, 4),
                    "confidence_lower": round(max(0.0, float(row["yhat_lower"])), 2),
                    "confidence_upper": round(float(row["yhat_upper"]), 2),
                    "horizon_hours": horizon,
                }
            )
        return results

    def _predict_fallback(self, weather_forecast: list[dict]) -> list[dict]:
        """Simple heuristic prediction when Prophet is not available."""
        assert self._fallback_avg_kwh is not None
        base = self._fallback_avg_kwh
        now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)

        weather_lookup: dict[str, dict] = {}
        for entry in weather_forecast:
            dt = _parse_datetime(entry["datetime"])
            key = dt.strftime("%Y-%m-%d %H")
            weather_lookup[key] = entry

        results: list[dict] = []
        for h in range(1, 49):
            target = now + timedelta(hours=h)
            hour = target.hour
            weekday = target.weekday()  # 0=Mon … 6=Sun

            multiplier = _HOUR_MULTIPLIERS.get(hour, 1.0)
            if weekday >= 5:
                multiplier *= _WEEKEND_FACTOR

            # Temperature adjustment: colder → more heating energy
            key = target.strftime("%Y-%m-%d %H")
            outdoor_temp = 15.0
            if key in weather_lookup:
                outdoor_temp = float(weather_lookup[key].get("outdoor_temp", 15.0))
            temp_factor = 1.0 + max(0.0, (15.0 - outdoor_temp) * 0.02)

            predicted_kwh = max(0.0, base * multiplier * temp_factor)
            noise_band = predicted_kwh * 0.15  # ±15 % confidence

            results.append(
                {
                    "forecast_date": target.isoformat(),
                    "predicted_kwh": round(predicted_kwh, 2),
                    "predicted_cost_eur": round(predicted_kwh * COST_EUR_PER_KWH, 4),
                    "confidence_lower": round(max(0.0, predicted_kwh - noise_band), 2),
                    "confidence_upper": round(predicted_kwh + noise_band, 2),
                    "horizon_hours": h,
                }
            )
        return results

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _prepare_training_data(readings: list[dict]) -> pd.DataFrame:
        """Convert raw readings to a Prophet-compatible DataFrame.

        Expected keys per reading: ``datetime``, ``energy_kwh``.
        Optional: ``outdoor_temp``, ``is_occupied``.
        """
        rows: list[dict] = []
        for r in readings:
            dt = _parse_datetime(r["datetime"])
            rows.append(
                {
                    "ds": dt,
                    "y": float(r["energy_kwh"]),
                    "outdoor_temp": float(r.get("outdoor_temp", 15.0)),
                    "is_occupied": 1.0 if r.get("is_occupied", False) else 0.0,
                }
            )
        df = pd.DataFrame(rows)
        df.sort_values("ds", inplace=True)
        df.reset_index(drop=True, inplace=True)
        return df


# ═══════════════════════════════════════════════════════════════════════════
# Module-level helpers
# ═══════════════════════════════════════════════════════════════════════════

def _parse_datetime(value: str | datetime) -> datetime:
    """Parse an ISO-8601 string or pass through a datetime object."""
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(value)


def generate_mock_forecast(site_id: str, days: int = 2) -> list[dict]:
    """Return a realistic mock forecast for demo / development purposes.

    Parameters
    ----------
    site_id:
        Identifier of the site (included for consistency with real API).
    days:
        Number of days to forecast (default 2 = 48 hours).

    Returns
    -------
    list[dict]
        Same schema as :meth:`EnergyForecaster.predict_next_48h`.
    """
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    hours = days * 24
    base_kwh = 42.0  # typical small commercial building

    results: list[dict] = []
    for h in range(1, hours + 1):
        target = now + timedelta(hours=h)
        hour = target.hour
        weekday = target.weekday()

        multiplier = _HOUR_MULTIPLIERS.get(hour, 1.0)
        if weekday >= 5:
            multiplier *= _WEEKEND_FACTOR

        # Add slight sinusoidal variation for realism
        variation = 1.0 + 0.05 * math.sin(2 * math.pi * h / 24)
        predicted_kwh = round(base_kwh * multiplier * variation, 2)
        noise_band = round(predicted_kwh * 0.12, 2)

        results.append(
            {
                "site_id": site_id,
                "forecast_date": target.isoformat(),
                "predicted_kwh": predicted_kwh,
                "predicted_cost_eur": round(predicted_kwh * COST_EUR_PER_KWH, 4),
                "confidence_lower": round(max(0.0, predicted_kwh - noise_band), 2),
                "confidence_upper": round(predicted_kwh + noise_band, 2),
                "horizon_hours": h,
            }
        )

    logger.debug("Generated mock forecast for site %s (%d hours)", site_id, hours)
    return results
