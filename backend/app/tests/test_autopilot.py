"""Tests for the autopilot safety validator, energy optimizer, and anomaly detector."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import pytest

from app.services.autopilot.safety import (
    FROST_PROTECTION_MIN_TEMP,
    MAX_TEMP_CHANGE_PER_ACTION,
    SafetyValidator,
)
from app.services.ml.anomaly import AnomalyDetector
from app.services.ml.optimization import EnergyOptimizer
from app.utils.calculations import calculate_heating_savings


# ---------------------------------------------------------------------------
# SafetyValidator
# ---------------------------------------------------------------------------


class TestSafetyValidator:
    """Unit tests for SafetyValidator.validate_actions."""

    @pytest.fixture()
    def validator(self) -> SafetyValidator:
        return SafetyValidator()

    @pytest.fixture()
    def sample_zones(self) -> list[dict]:
        return [
            {
                "id": "zone-1",
                "target_temp_min": 19.0,
                "target_temp_max": 23.0,
            }
        ]

    @pytest.fixture()
    def sample_devices(self) -> list[dict]:
        return [
            {
                "id": "device-1",
                "zone_id": "zone-1",
                "device_type": "thermostat",
            }
        ]

    def test_temperature_bounds_rejected(
        self,
        validator: SafetyValidator,
        sample_zones: list[dict],
        sample_devices: list[dict],
    ) -> None:
        """An action targeting a temperature outside zone bounds must be rejected."""
        actions = [
            {
                "device_id": "device-1",
                "action_type": "temperature_adjustment",
                "action_params": {"target_temperature": 25.0},  # above max 23
            }
        ]
        safe, rejected = validator.validate_actions(actions, sample_zones, sample_devices)
        assert len(rejected) == 1
        assert len(safe) == 0
        assert "exceeds zone maximum" in rejected[0]["error_message"]

    def test_temperature_bounds_below_min(
        self,
        validator: SafetyValidator,
        sample_zones: list[dict],
        sample_devices: list[dict],
    ) -> None:
        """An action targeting a temperature below zone min must be rejected."""
        actions = [
            {
                "device_id": "device-1",
                "action_type": "temperature_adjustment",
                "action_params": {"target_temperature": 17.0},  # below min 19
            }
        ]
        safe, rejected = validator.validate_actions(actions, sample_zones, sample_devices)
        assert len(rejected) == 1
        assert "below zone minimum" in rejected[0]["error_message"]

    def test_temperature_within_bounds_accepted(
        self,
        validator: SafetyValidator,
        sample_zones: list[dict],
        sample_devices: list[dict],
    ) -> None:
        """An action within zone bounds should be accepted."""
        actions = [
            {
                "device_id": "device-1",
                "action_type": "temperature_adjustment",
                "action_params": {
                    "target_temperature": 21.0,
                    "temperature_delta": 1.0,
                },
            }
        ]
        safe, rejected = validator.validate_actions(actions, sample_zones, sample_devices)
        assert len(safe) == 1
        assert len(rejected) == 0

    def test_frost_protection(
        self,
        validator: SafetyValidator,
        sample_zones: list[dict],
        sample_devices: list[dict],
    ) -> None:
        """Frost protection: target below 16 degrees C must be rejected."""
        # Use a zone with a very low min to bypass the bounds check first.
        zones_wide = [
            {"id": "zone-1", "target_temp_min": 10.0, "target_temp_max": 30.0}
        ]
        actions = [
            {
                "device_id": "device-1",
                "action_type": "temperature_adjustment",
                "action_params": {
                    "target_temperature": 14.0,  # below FROST_PROTECTION_MIN_TEMP (16)
                    "temperature_delta": 1.0,
                },
            }
        ]
        safe, rejected = validator.validate_actions(actions, zones_wide, sample_devices)
        assert len(rejected) == 1
        assert "frost protection" in rejected[0]["error_message"].lower()

    def test_max_change_rejected(
        self,
        validator: SafetyValidator,
        sample_zones: list[dict],
        sample_devices: list[dict],
    ) -> None:
        """A temperature delta exceeding MAX_TEMP_CHANGE_PER_ACTION must be rejected."""
        zones_wide = [
            {"id": "zone-1", "target_temp_min": 15.0, "target_temp_max": 30.0}
        ]
        actions = [
            {
                "device_id": "device-1",
                "action_type": "temperature_adjustment",
                "action_params": {
                    "target_temperature": 20.0,
                    "temperature_delta": 3.0,  # > MAX_TEMP_CHANGE_PER_ACTION (2.0)
                },
            }
        ]
        safe, rejected = validator.validate_actions(actions, zones_wide, sample_devices)
        assert len(rejected) == 1
        assert "exceeds the maximum" in rejected[0]["error_message"]


# ---------------------------------------------------------------------------
# EnergyOptimizer
# ---------------------------------------------------------------------------


class TestEnergyOptimizer:
    """Unit tests for the rule-based EnergyOptimizer."""

    def _make_optimizer(self) -> EnergyOptimizer:
        zones = [
            {
                "zone_id": "z1",
                "name": "Open Space",
                "surface_m2": 200,
                "target_temp": 21.0,
                "target_temp_min": 19.0,
                "is_critical": False,
                "occupancy_schedule": {
                    "0": [{"start": 8, "end": 18}],
                    "1": [{"start": 8, "end": 18}],
                    "2": [{"start": 8, "end": 18}],
                    "3": [{"start": 8, "end": 18}],
                    "4": [{"start": 8, "end": 18}],
                },
            }
        ]
        devices = [
            {
                "device_id": "d1",
                "zone_id": "z1",
                "device_type": "hvac",
                "is_controllable": True,
            }
        ]
        return EnergyOptimizer(
            site_id="site-test",
            site_surface=200,
            zones=zones,
            devices=devices,
        )

    def test_optimizer_peak_tariff(self) -> None:
        """Peak-approaching hour (7, since 8 is peak start) should trigger reduce_setpoint."""
        optimizer = self._make_optimizer()
        readings = {
            "indoor_temp": 21.0,
            "outdoor_temp": 10.0,
            "current_hour": 7,    # one hour before peak (8-13)
            "current_weekday": 1,  # Tuesday
        }
        weather = {"sunshine_pct_next_6h": 30, "min_temp_tonight": 10.0}
        tariff = {"off_peak_end_hour": 6}

        actions = asyncio.get_event_loop().run_until_complete(
            optimizer.decide_actions(readings, weather, tariff)
        )

        # Should include a reduce_setpoint for peak-approaching.
        peak_actions = [a for a in actions if a["action_type"] == "reduce_setpoint"]
        assert len(peak_actions) >= 1
        assert peak_actions[0]["predicted_savings_eur"] > 0

    def test_optimizer_unoccupied_zone(self) -> None:
        """An unoccupied zone on a weekend should trigger eco mode."""
        optimizer = self._make_optimizer()
        readings = {
            "indoor_temp": 21.0,
            "outdoor_temp": 12.0,
            "current_hour": 14,   # afternoon
            "current_weekday": 6,  # Sunday -- no occupancy scheduled
        }
        weather = {"sunshine_pct_next_6h": 30, "min_temp_tonight": 8.0}
        tariff = {"off_peak_end_hour": 6}

        actions = asyncio.get_event_loop().run_until_complete(
            optimizer.decide_actions(readings, weather, tariff)
        )

        eco_actions = [a for a in actions if a["action_type"] == "set_eco_mode"]
        assert len(eco_actions) >= 1
        assert eco_actions[0]["predicted_savings_kwh"] > 0


# ---------------------------------------------------------------------------
# AnomalyDetector
# ---------------------------------------------------------------------------


class TestAnomalyDetector:
    """Unit tests for AnomalyDetector."""

    def test_anomaly_detected(self) -> None:
        """Readings with power > 130% of baseline should be flagged."""
        detector = AnomalyDetector(site_id="site-test")

        baseline = [
            {"time": datetime(2025, 1, 6, h, 0, tzinfo=timezone.utc), "power_kw": 5.0}
            for h in range(24)
        ]
        recent = [
            {
                "time": datetime(2025, 1, 13, 10, 0, tzinfo=timezone.utc),
                "device_id": "d1",
                "power_kw": 7.5,  # 50% above baseline of 5.0
            },
        ]

        anomalies = detector.detect_anomalies(recent, baseline)
        assert len(anomalies) == 1
        assert anomalies[0]["severity"] == "critical"  # >50%
        assert anomalies[0]["deviation_pct"] == 50.0

    def test_no_anomalies_for_normal_readings(self) -> None:
        """Readings within 130% of baseline should NOT be flagged."""
        detector = AnomalyDetector(site_id="site-test")

        baseline = [
            {"time": datetime(2025, 1, 6, h, 0, tzinfo=timezone.utc), "power_kw": 5.0}
            for h in range(24)
        ]
        recent = [
            {
                "time": datetime(2025, 1, 13, 10, 0, tzinfo=timezone.utc),
                "device_id": "d1",
                "power_kw": 5.5,  # only 10% above baseline
            },
        ]

        anomalies = detector.detect_anomalies(recent, baseline)
        assert len(anomalies) == 0


# ---------------------------------------------------------------------------
# Savings calculation
# ---------------------------------------------------------------------------


class TestSavingsCalculation:
    """Unit test for calculate_heating_savings helper."""

    def test_savings_calculation(self) -> None:
        """Verify the formula: baseline_kwh * savings_fraction."""
        result = calculate_heating_savings(
            temp_reduction=1.0,
            duration_hours=10.0,
            surface_m2=100.0,
        )
        # baseline_kwh = (50 * 100 * 10) / 1000 = 50 kWh
        # savings_fraction = 1.0 * 0.07 = 0.07
        # kwh_saved = 50 * 0.07 = 3.5
        assert result["kwh_saved"] == 3.5
        # eur_saved = 3.5 * 0.2016 = 0.7056
        assert result["eur_saved"] == 0.7056
        # co2_saved = 3.5 * 0.0569 = 0.19915 -> rounded to 0.1992
        assert result["co2_saved"] == pytest.approx(0.1992, abs=0.001)
