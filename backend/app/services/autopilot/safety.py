"""Safety validation layer for the Autopilot engine.

Every action proposed by the ML optimizer is validated against a set of
hard-coded safety rules before it is sent to the device.  Actions that
violate any rule are moved to a *rejected* list with a human-readable
``error_message`` explaining the reason.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any

logger = logging.getLogger(__name__)

# ── Safety constants ─────────────────────────────────────────────────────
FROST_PROTECTION_MIN_TEMP: float = 16.0
MAX_TEMP_CHANGE_PER_ACTION: float = 2.0
MAX_TEMP_CHANGES_PER_HOUR: int = 3


class SafetyValidator:
    """Validate autopilot actions against safety rules.

    The validator is stateless and can be reused across multiple runs.
    """

    # ── Public API ───────────────────────────────────────────────────────

    def validate_actions(
        self,
        actions: list[dict],
        zones: list[dict],
        devices: list[dict],
    ) -> tuple[list[dict], list[dict]]:
        """Partition *actions* into safe and rejected lists.

        Parameters
        ----------
        actions:
            List of proposed action dicts from the optimizer.  Each dict is
            expected to contain at least ``device_id``, ``action_type``, and
            ``action_params``.
        zones:
            List of zone dicts (or serialised Zone models) with
            ``id``, ``target_temp_min``, and ``target_temp_max``.
        devices:
            List of device dicts (or serialised Device models) with at least
            ``id``, ``zone_id``, and ``device_type``.

        Returns
        -------
        tuple[list[dict], list[dict]]
            ``(safe_actions, rejected_actions)``.  Rejected actions have
            ``status`` set to ``"failed"`` and an ``error_message`` field.
        """
        safe_actions: list[dict] = []
        rejected_actions: list[dict] = []

        # Build lookup maps for fast access.
        zone_map: dict[str, dict] = {z["id"]: z for z in zones}
        device_map: dict[str, dict] = {d["id"]: d for d in devices}

        # Track actions already accepted in *this* batch so the rate limiter
        # can account for them.
        recent_accepted: list[dict] = []

        for action in actions:
            device = device_map.get(action.get("device_id", ""))
            zone_id = device.get("zone_id") if device else None
            zone = zone_map.get(zone_id) if zone_id else None

            rejected = False
            reason = ""

            # Rule (a): Temperature bounds.
            if zone and action.get("action_type") == "temperature_adjustment":
                ok, msg = self._check_temperature_bounds(action, zone)
                if not ok:
                    rejected, reason = True, msg

            # Rule (b): Cannot shut down critical HVAC in extreme weather.
            if not rejected and action.get("action_type") == "equipment_shutdown":
                if device and device.get("device_type") == "hvac":
                    rejected = True
                    reason = (
                        "Cannot shut down critical HVAC equipment; "
                        "extreme-weather protection is active."
                    )
                    logger.warning(
                        "safety.critical_shutdown_blocked",
                        extra={
                            "device_id": action.get("device_id"),
                            "action_type": action.get("action_type"),
                        },
                    )

            # Rule (c): Rate limiting (max changes per device per hour).
            if not rejected and action.get("action_type") == "temperature_adjustment":
                ok, msg = self._check_rate_limit(action, recent_accepted)
                if not ok:
                    rejected, reason = True, msg

            # Rule (d): Frost protection.
            if not rejected and action.get("action_type") == "temperature_adjustment":
                ok, msg = self._check_frost_protection(action)
                if not ok:
                    rejected, reason = True, msg

            # Rule (e): Maximum single-action delta.
            if not rejected and action.get("action_type") == "temperature_adjustment":
                params = action.get("action_params") or {}
                delta = abs(params.get("temperature_delta", 0.0))
                if delta > MAX_TEMP_CHANGE_PER_ACTION:
                    rejected = True
                    reason = (
                        f"Temperature change of {delta}°C exceeds the maximum "
                        f"allowed single-action delta of "
                        f"{MAX_TEMP_CHANGE_PER_ACTION}°C."
                    )

            # Dispatch to safe or rejected.
            if rejected:
                action["status"] = "failed"
                action["error_message"] = reason
                rejected_actions.append(action)
                logger.info(
                    "safety.action_rejected",
                    extra={
                        "device_id": action.get("device_id"),
                        "reason": reason,
                    },
                )
            else:
                safe_actions.append(action)
                recent_accepted.append(action)

        logger.info(
            "safety.validation_complete",
            extra={
                "total": len(actions),
                "safe": len(safe_actions),
                "rejected": len(rejected_actions),
            },
        )
        return safe_actions, rejected_actions

    # ── Private validation helpers ───────────────────────────────────────

    def _check_temperature_bounds(
        self,
        action: dict,
        zone: dict,
    ) -> tuple[bool, str]:
        """Return ``(True, "")`` if the target temperature stays within zone bounds.

        Parameters
        ----------
        action:
            Action dict with ``action_params.target_temperature``.
        zone:
            Zone dict with ``target_temp_min`` and ``target_temp_max``.

        Returns
        -------
        tuple[bool, str]
            ``(is_valid, error_message)``.
        """
        params = action.get("action_params") or {}
        target_temp = params.get("target_temperature")

        if target_temp is None:
            return True, ""

        temp_min = zone.get("target_temp_min", 16.0)
        temp_max = zone.get("target_temp_max", 26.0)

        if target_temp < temp_min:
            return (
                False,
                f"Target temperature {target_temp}°C is below zone minimum "
                f"of {temp_min}°C.",
            )
        if target_temp > temp_max:
            return (
                False,
                f"Target temperature {target_temp}°C exceeds zone maximum "
                f"of {temp_max}°C.",
            )
        return True, ""

    def _check_rate_limit(
        self,
        action: dict,
        recent_actions: list[dict],
    ) -> tuple[bool, str]:
        """Ensure no more than ``MAX_TEMP_CHANGES_PER_HOUR`` temperature
        adjustments are applied to the same device within the current batch.

        Parameters
        ----------
        action:
            The candidate action.
        recent_actions:
            Actions already accepted during this validation pass (same batch).

        Returns
        -------
        tuple[bool, str]
            ``(is_valid, error_message)``.
        """
        device_id = action.get("device_id")
        same_device_count = sum(
            1
            for a in recent_actions
            if a.get("device_id") == device_id
            and a.get("action_type") == "temperature_adjustment"
        )

        if same_device_count >= MAX_TEMP_CHANGES_PER_HOUR:
            return (
                False,
                f"Rate limit exceeded: device {device_id} already has "
                f"{same_device_count} temperature changes in this cycle "
                f"(max {MAX_TEMP_CHANGES_PER_HOUR}/hour).",
            )
        return True, ""

    def _check_frost_protection(
        self,
        action: dict,
    ) -> tuple[bool, str]:
        """Ensure the target temperature never drops below the frost
        protection floor.

        Parameters
        ----------
        action:
            Action dict with ``action_params.target_temperature``.

        Returns
        -------
        tuple[bool, str]
            ``(is_valid, error_message)``.
        """
        params = action.get("action_params") or {}
        target_temp = params.get("target_temperature")

        if target_temp is not None and target_temp < FROST_PROTECTION_MIN_TEMP:
            return (
                False,
                f"Target temperature {target_temp}°C is below the frost "
                f"protection floor of {FROST_PROTECTION_MIN_TEMP}°C.",
            )
        return True, ""
