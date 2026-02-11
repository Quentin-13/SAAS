"""Energy optimisation decision engine.

Evaluates a rule-based set of actions (peak-tariff avoidance, predictive
thermal optimisation, occupancy-based control, night setback) and returns
concrete device actions with estimated savings.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Physical / tariff constants
# ---------------------------------------------------------------------------
COST_EUR_PER_KWH: float = 0.2016
HEATING_WATTS_PER_M2: float = 50.0  # average heating power density
SAVINGS_PER_DEGREE_PCT: float = 0.07  # 1 °C reduction ≈ 7 % savings
FROST_PROTECTION_TEMP: float = 16.0  # minimum night setback temperature

# French regulated peak-tariff hours
_PEAK_RANGES: list[tuple[int, int]] = [(8, 13), (17, 20)]

# Night setback window (office buildings)
_NIGHT_START: int = 20
_NIGHT_END: int = 6


class EnergyOptimizer:
    """Rule-based energy optimisation engine for a building site.

    Parameters
    ----------
    site_id:
        Unique identifier for the site.
    site_surface:
        Total heated surface in m².
    zones:
        List of zone dicts.  Each zone is expected to contain at minimum:
        ``zone_id``, ``name``, ``surface_m2``, ``target_temp``,
        ``target_temp_min``, ``is_critical`` (bool), and
        ``occupancy_schedule`` (dict mapping weekday 0-6 to list of
        ``{"start": HH, "end": HH}`` intervals).
    devices:
        List of controllable device dicts.  Each device has ``device_id``,
        ``zone_id``, ``device_type`` (e.g. ``"hvac"``, ``"lighting"``),
        and ``is_controllable`` (bool).
    """

    def __init__(
        self,
        site_id: str,
        site_surface: int,
        zones: list[dict],
        devices: list[dict],
    ) -> None:
        self.site_id = site_id
        self.site_surface = site_surface
        self.zones = {z["zone_id"]: z for z in zones}
        self.devices = devices
        logger.info(
            "EnergyOptimizer initialised for site %s (%d m², %d zones, %d devices)",
            site_id,
            site_surface,
            len(zones),
            len(devices),
        )

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    async def decide_actions(
        self,
        current_readings: dict,
        weather: dict,
        tariff_schedule: dict,
    ) -> list[dict]:
        """Evaluate all optimisation rules and return recommended actions.

        Parameters
        ----------
        current_readings:
            Dict with at least ``indoor_temp`` (float), ``outdoor_temp``
            (float), ``current_hour`` (int 0-23), ``current_weekday``
            (int 0=Mon…6=Sun).
        weather:
            Dict with ``sunshine_pct_next_6h`` (0-100), ``min_temp_tonight``
            (float °C).
        tariff_schedule:
            Dict with optional ``off_peak_end_hour`` (int, default 6).

        Returns
        -------
        list[dict]
            Each entry describes a recommended action.
        """
        actions: list[dict] = []
        current_hour: int = int(current_readings.get("current_hour", datetime.now(timezone.utc).hour))
        current_weekday: int = int(current_readings.get("current_weekday", datetime.now(timezone.utc).weekday()))
        off_peak_end: int = int(tariff_schedule.get("off_peak_end_hour", 6))

        for device in self.devices:
            if not device.get("is_controllable", False):
                continue

            zone_id: str = device.get("zone_id", "")
            zone: dict = self.zones.get(zone_id, {})
            zone_surface: float = float(zone.get("surface_m2", self.site_surface / max(len(self.zones), 1)))
            target_temp: float = float(zone.get("target_temp", 21.0))
            target_temp_min: float = float(zone.get("target_temp_min", 19.0))
            is_critical: bool = bool(zone.get("is_critical", False))

            # ── Rule 1 – Peak tariff avoidance ───────────────────────
            if self._is_peak_approaching(current_hour) and not is_critical:
                reduction = 1.0
                savings = self._calculate_savings(reduction, duration_hours=1.0, surface_m2=zone_surface)
                actions.append(
                    {
                        "device_id": device["device_id"],
                        "action_type": "reduce_setpoint",
                        "action_params": {
                            "target_temp": target_temp - reduction,
                            "reduction_c": reduction,
                        },
                        "reasoning": (
                            f"Période tarifaire de pointe imminente — réduction de {reduction} °C "
                            f"dans la zone « {zone.get('name', zone_id)} » pour limiter la consommation."
                        ),
                        "predicted_savings_eur": savings["savings_eur"],
                        "predicted_savings_kwh": savings["savings_kwh"],
                        "confidence_score": 0.85,
                    }
                )

            # ── Rule 2 – Predictive thermal optimisation ─────────────
            sunshine_pct: float = float(weather.get("sunshine_pct_next_6h", 0))
            min_temp_tonight: float = float(weather.get("min_temp_tonight", 10.0))

            if sunshine_pct > 70:
                reduction = 0.5
                savings = self._calculate_savings(reduction, duration_hours=4.0, surface_m2=zone_surface)
                actions.append(
                    {
                        "device_id": device["device_id"],
                        "action_type": "reduce_setpoint",
                        "action_params": {
                            "target_temp": target_temp - reduction,
                            "reduction_c": reduction,
                            "reason_code": "solar_gain",
                        },
                        "reasoning": (
                            f"Ensoleillement prévu à {sunshine_pct:.0f} % dans les 6 prochaines heures — "
                            f"réduction de {reduction} °C pour compenser l'apport solaire."
                        ),
                        "predicted_savings_eur": savings["savings_eur"],
                        "predicted_savings_kwh": savings["savings_kwh"],
                        "confidence_score": 0.70,
                    }
                )

            if min_temp_tonight < 2.0 and current_hour >= (off_peak_end - 2) and current_hour < off_peak_end:
                increase = 1.0
                # Pre-heating costs energy but avoids peak consumption later
                extra = self._calculate_savings(increase, duration_hours=2.0, surface_m2=zone_surface)
                actions.append(
                    {
                        "device_id": device["device_id"],
                        "action_type": "increase_setpoint",
                        "action_params": {
                            "target_temp": target_temp + increase,
                            "increase_c": increase,
                            "reason_code": "cold_night_preheat",
                        },
                        "reasoning": (
                            f"Nuit très froide prévue ({min_temp_tonight:.1f} °C) — "
                            f"préchauffage de +{increase} °C avant la fin des heures creuses "
                            f"pour éviter un appel de puissance en pointe."
                        ),
                        "predicted_savings_eur": extra["savings_eur"],
                        "predicted_savings_kwh": extra["savings_kwh"],
                        "confidence_score": 0.65,
                    }
                )

            # ── Rule 3 – Occupancy-based control ─────────────────────
            zone_occupied = self._is_zone_occupied(zone, current_hour, current_weekday)
            about_to_be_occupied = self._is_zone_occupied(zone, (current_hour + 1) % 24, current_weekday)

            if not zone_occupied and not about_to_be_occupied:
                eco_temp = target_temp_min - 2.0
                reduction = target_temp - eco_temp
                if reduction > 0:
                    savings = self._calculate_savings(reduction, duration_hours=1.0, surface_m2=zone_surface)
                    actions.append(
                        {
                            "device_id": device["device_id"],
                            "action_type": "set_eco_mode",
                            "action_params": {
                                "target_temp": eco_temp,
                                "reduction_c": reduction,
                            },
                            "reasoning": (
                                f"Zone « {zone.get('name', zone_id)} » actuellement inoccupée — "
                                f"passage en mode éco ({eco_temp:.1f} °C)."
                            ),
                            "predicted_savings_eur": savings["savings_eur"],
                            "predicted_savings_kwh": savings["savings_kwh"],
                            "confidence_score": 0.90,
                        }
                    )
            elif not zone_occupied and about_to_be_occupied:
                # Pre-heat: zone will be occupied within ~30 min
                actions.append(
                    {
                        "device_id": device["device_id"],
                        "action_type": "pre_heat",
                        "action_params": {
                            "target_temp": target_temp,
                            "reason_code": "occupancy_preheat",
                        },
                        "reasoning": (
                            f"Zone « {zone.get('name', zone_id)} » sera occupée dans moins de 30 min — "
                            "lancement du préchauffage au point de consigne normal."
                        ),
                        "predicted_savings_eur": 0.0,
                        "predicted_savings_kwh": 0.0,
                        "confidence_score": 0.80,
                    }
                )

            # ── Rule 4 – Night setback ───────────────────────────────
            if current_hour >= _NIGHT_START or current_hour < _NIGHT_END:
                if target_temp > FROST_PROTECTION_TEMP:
                    reduction = target_temp - FROST_PROTECTION_TEMP
                    night_hours = (_NIGHT_END + 24 - _NIGHT_START) if _NIGHT_END < _NIGHT_START else (_NIGHT_END - _NIGHT_START)
                    savings = self._calculate_savings(reduction, duration_hours=float(night_hours), surface_m2=zone_surface)
                    actions.append(
                        {
                            "device_id": device["device_id"],
                            "action_type": "night_setback",
                            "action_params": {
                                "target_temp": FROST_PROTECTION_TEMP,
                                "reduction_c": reduction,
                            },
                            "reasoning": (
                                f"Période nocturne (bureaux) — abaissement à {FROST_PROTECTION_TEMP:.0f} °C "
                                f"(protection antigel) dans la zone « {zone.get('name', zone_id)} »."
                            ),
                            "predicted_savings_eur": savings["savings_eur"],
                            "predicted_savings_kwh": savings["savings_kwh"],
                            "confidence_score": 0.95,
                        }
                    )

        logger.info(
            "Optimisation run for site %s produced %d actions",
            self.site_id,
            len(actions),
        )
        return actions

    # ------------------------------------------------------------------
    # Savings estimation
    # ------------------------------------------------------------------

    @staticmethod
    def _calculate_savings(
        temp_reduction: float,
        duration_hours: float,
        surface_m2: float,
    ) -> dict[str, float]:
        """Estimate energy and cost savings from a temperature reduction.

        Assumptions
        -----------
        * 1 °C reduction ≈ 7 % energy savings.
        * Average heating demand = 50 W/m².
        * Electricity cost = 0.2016 €/kWh.

        Returns a dict with ``savings_kwh`` and ``savings_eur``.
        """
        base_consumption_kwh = (HEATING_WATTS_PER_M2 * surface_m2 * duration_hours) / 1000.0
        savings_kwh = base_consumption_kwh * SAVINGS_PER_DEGREE_PCT * temp_reduction
        savings_eur = savings_kwh * COST_EUR_PER_KWH
        return {
            "savings_kwh": round(savings_kwh, 3),
            "savings_eur": round(savings_eur, 4),
        }

    # ------------------------------------------------------------------
    # Tariff helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _is_peak_tariff(hour: int) -> bool:
        """Return True if *hour* falls within French peak-tariff periods.

        Peak hours: 08:00-13:00 and 17:00-20:00.
        """
        return any(start <= hour < end for start, end in _PEAK_RANGES)

    def _is_peak_approaching(self, current_hour: int) -> bool:
        """Return True if a peak period starts within the next hour."""
        next_hour = (current_hour + 1) % 24
        return not self._is_peak_tariff(current_hour) and self._is_peak_tariff(next_hour)

    # ------------------------------------------------------------------
    # Occupancy helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _is_zone_occupied(zone: dict, current_hour: int, current_weekday: int) -> bool:
        """Check whether *zone* is occupied at the given hour and weekday.

        The ``occupancy_schedule`` is a dict mapping weekday (0-6) to a list
        of ``{"start": int, "end": int}`` intervals (hours).
        """
        schedule: dict[int | str, Any] = zone.get("occupancy_schedule", {})
        # Accept both int keys and string keys (JSON often serialises keys as strings)
        day_slots = schedule.get(current_weekday) or schedule.get(str(current_weekday), [])
        for slot in day_slots:
            start = int(slot.get("start", 0))
            end = int(slot.get("end", 0))
            if start <= current_hour < end:
                return True
        return False
