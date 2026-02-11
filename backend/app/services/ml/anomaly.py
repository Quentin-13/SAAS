"""Anomaly detection service for energy consumption."""
import logging
import random
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """Detects abnormal energy consumption patterns."""

    def __init__(self, site_id: str):
        self.site_id = site_id

    def detect_anomalies(
        self,
        recent_readings: list[dict],
        baseline_readings: list[dict],
    ) -> list[dict]:
        """Detect overconsumption anomalies by comparing recent vs baseline.

        Args:
            recent_readings: Last 24h of readings [{time, device_id, power_kw, ...}]
            baseline_readings: Historical readings for same weekday over past 4 weeks

        Returns:
            List of anomalies with deviation details
        """
        baseline = self._calculate_baseline(baseline_readings)
        anomalies = []

        for reading in recent_readings:
            hour = reading.get("time")
            if isinstance(hour, datetime):
                hour = hour.hour
            elif isinstance(hour, str):
                try:
                    hour = datetime.fromisoformat(hour).hour
                except (ValueError, TypeError):
                    continue

            expected = baseline.get(hour, 0)
            if expected <= 0:
                continue

            actual = reading.get("power_kw", 0)
            if actual <= 0:
                continue

            deviation_pct = ((actual / expected) - 1) * 100

            if deviation_pct > 30:
                severity = "critical" if deviation_pct > 50 else "warning"
                waste_kwh = (actual - expected) * 0.25  # 15-min interval
                anomalies.append({
                    "time": reading.get("time"),
                    "device_id": reading.get("device_id", "unknown"),
                    "actual_kw": round(actual, 2),
                    "expected_kw": round(expected, 2),
                    "deviation_pct": round(deviation_pct, 1),
                    "estimated_waste_eur": round(waste_kwh * 0.2016, 2),
                    "severity": severity,
                })

        logger.info(
            "Anomaly detection complete",
            extra={"site_id": self.site_id, "anomalies_found": len(anomalies)},
        )
        return anomalies

    def _calculate_baseline(self, readings: list[dict]) -> dict[int, float]:
        """Calculate average power_kw per hour from historical readings."""
        hourly_sums: dict[int, list[float]] = {}

        for reading in readings:
            hour = reading.get("time")
            if isinstance(hour, datetime):
                hour = hour.hour
            elif isinstance(hour, str):
                try:
                    hour = datetime.fromisoformat(hour).hour
                except (ValueError, TypeError):
                    continue

            power = reading.get("power_kw", 0)
            if power > 0:
                hourly_sums.setdefault(hour, []).append(power)

        return {
            hour: round(sum(values) / len(values), 2)
            for hour, values in hourly_sums.items()
            if values
        }


def generate_mock_anomalies(site_id: str) -> list[dict]:
    """Generate realistic mock anomalies for demo."""
    now = datetime.now()
    return [
        {
            "time": (now - timedelta(hours=3)).isoformat(),
            "device_id": "device-hvac-001",
            "actual_kw": 8.5,
            "expected_kw": 5.2,
            "deviation_pct": 63.5,
            "estimated_waste_eur": 0.17,
            "severity": "critical",
            "description": "HVAC en surconsommation pendant la pause déjeuner",
        },
        {
            "time": (now - timedelta(hours=8)).isoformat(),
            "device_id": "device-lighting-001",
            "actual_kw": 2.1,
            "expected_kw": 0.3,
            "deviation_pct": 600.0,
            "estimated_waste_eur": 0.09,
            "severity": "critical",
            "description": "Éclairage resté allumé pendant la nuit",
        },
        {
            "time": (now - timedelta(hours=1)).isoformat(),
            "device_id": "device-therm-001",
            "actual_kw": 4.2,
            "expected_kw": 3.1,
            "deviation_pct": 35.5,
            "estimated_waste_eur": 0.06,
            "severity": "warning",
            "description": "Chauffage légèrement au-dessus de la normale",
        },
    ]
