"""Autopilot engine — main orchestration module.

Executed every 15 minutes by a Celery beat task, the engine runs a full
optimisation cycle for a single site:

1. Load site, zones, and devices from the database.
2. Fetch current weather conditions.
3. Gather current device states.
4. Ask the ML optimizer for recommended actions.
5. Validate those actions through the safety layer.
6. Execute the safe actions via brand-specific integrations.
7. Persist every action (executed *and* rejected) to the database.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models import AutopilotAction, Device, Site, Zone
from app.services.autopilot.actions import ActionExecutor
from app.services.autopilot.safety import SafetyValidator
from app.services.integrations.weather import WeatherClient
from app.services.ml.optimization import EnergyOptimizer

logger = logging.getLogger(__name__)


class AutopilotEngine:
    """Main autopilot orchestration engine.

    Parameters
    ----------
    db:
        Active SQLAlchemy session used for reads **and** writes within a
        single Celery task execution.
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self.safety_validator = SafetyValidator()
        self.action_executor = ActionExecutor(db)
        self.weather_client = WeatherClient()
        self.optimizer = EnergyOptimizer()

    # ── Public API ───────────────────────────────────────────────────────

    async def run(self, site_id: str) -> list[dict]:
        """Run a full autopilot cycle for the given site.

        Parameters
        ----------
        site_id:
            Primary key of the :class:`Site` to optimise.

        Returns
        -------
        list[dict]
            List of executed action dicts (status == ``"executed"``).
        """
        logger.info("autopilot.cycle_start", extra={"site_id": site_id})

        # ── Step (a): Load site with zones and devices ───────────────────
        site: Site | None = self.db.query(Site).filter(Site.id == site_id).first()

        if site is None:
            logger.error("autopilot.site_not_found", extra={"site_id": site_id})
            return []

        # ── Step (b): Check autopilot flag ───────────────────────────────
        if not site.autopilot_enabled:
            logger.info(
                "autopilot.disabled",
                extra={"site_id": site_id, "site_name": site.name},
            )
            return []

        zones: list[Zone] = list(site.zones)
        devices: list[Device] = list(site.devices)

        logger.info(
            "autopilot.site_loaded",
            extra={
                "site_id": site_id,
                "zone_count": len(zones),
                "device_count": len(devices),
            },
        )

        # ── Step (c): Fetch current weather ──────────────────────────────
        weather: dict[str, Any] = {}
        try:
            weather = await self.weather_client.get_current(
                latitude=site.latitude,
                longitude=site.longitude,
            )
            logger.info(
                "autopilot.weather_fetched",
                extra={"site_id": site_id, "weather": weather},
            )
        except Exception as exc:
            logger.warning(
                "autopilot.weather_fetch_failed",
                extra={"site_id": site_id, "error": str(exc)},
            )

        # ── Step (d): Gather current device states ───────────────────────
        device_data: list[dict] = self._serialize_devices(devices)
        zone_data: list[dict] = self._serialize_zones(zones)

        logger.debug(
            "autopilot.device_states_collected",
            extra={"site_id": site_id, "devices": len(device_data)},
        )

        # ── Step (e): Ask optimizer for recommended actions ──────────────
        proposed_actions: list[dict] = []
        try:
            proposed_actions = await self.optimizer.decide_actions(
                site_id=site_id,
                zones=zone_data,
                devices=device_data,
                weather=weather,
            )
            logger.info(
                "autopilot.optimizer_done",
                extra={
                    "site_id": site_id,
                    "proposed_count": len(proposed_actions),
                },
            )
        except Exception as exc:
            logger.exception(
                "autopilot.optimizer_error",
                extra={"site_id": site_id, "error": str(exc)},
            )
            return []

        if not proposed_actions:
            logger.info("autopilot.no_actions_proposed", extra={"site_id": site_id})
            return []

        # ── Step (f): Safety validation ──────────────────────────────────
        safe_actions, rejected_actions = self.safety_validator.validate_actions(
            actions=proposed_actions,
            zones=zone_data,
            devices=device_data,
        )

        logger.info(
            "autopilot.safety_validation_done",
            extra={
                "site_id": site_id,
                "safe": len(safe_actions),
                "rejected": len(rejected_actions),
            },
        )

        # ── Step (g): Execute safe actions ───────────────────────────────
        device_map: dict[str, dict] = {d["id"]: d for d in device_data}
        executed_actions: list[dict] = []

        for action in safe_actions:
            device_info = device_map.get(action.get("device_id", ""), {})
            result = await self.action_executor.execute(action, device_info)
            executed_actions.append(result)

        logger.info(
            "autopilot.execution_done",
            extra={
                "site_id": site_id,
                "executed": sum(
                    1 for a in executed_actions if a.get("status") == "executed"
                ),
                "failed_at_execution": sum(
                    1 for a in executed_actions if a.get("status") == "failed"
                ),
            },
        )

        # ── Step (h): Persist all actions to the database ────────────────
        all_actions = executed_actions + rejected_actions
        self._save_actions(site_id, all_actions)

        # ── Step (i): Return executed actions ────────────────────────────
        successful = [a for a in executed_actions if a.get("status") == "executed"]

        logger.info(
            "autopilot.cycle_complete",
            extra={
                "site_id": site_id,
                "total_proposed": len(proposed_actions),
                "total_executed": len(successful),
                "total_rejected": len(rejected_actions),
            },
        )

        return successful

    # ── Private helpers ──────────────────────────────────────────────────

    def _serialize_devices(self, devices: list[Device]) -> list[dict]:
        """Convert ORM Device objects to plain dicts for downstream layers."""
        return [
            {
                "id": d.id,
                "site_id": d.site_id,
                "zone_id": d.zone_id,
                "device_type": d.device_type,
                "brand": d.brand,
                "model": d.model,
                "external_id": d.external_id,
                "name": d.name,
                "is_controllable": d.is_controllable,
                "is_active": d.is_active,
                "capabilities": d.capabilities,
                "current_state": d.current_state,
                "api_credentials": d.api_credentials,
            }
            for d in devices
        ]

    def _serialize_zones(self, zones: list[Zone]) -> list[dict]:
        """Convert ORM Zone objects to plain dicts for downstream layers."""
        return [
            {
                "id": z.id,
                "site_id": z.site_id,
                "name": z.name,
                "zone_type": z.zone_type,
                "surface_area": z.surface_area,
                "target_temp_min": z.target_temp_min,
                "target_temp_max": z.target_temp_max,
                "occupancy_schedule": z.occupancy_schedule,
            }
            for z in zones
        ]

    def _save_actions(self, site_id: str, actions: list[dict]) -> None:
        """Persist a list of action dicts as ``AutopilotAction`` records."""
        for action in actions:
            record = AutopilotAction(
                site_id=site_id,
                device_id=action.get("device_id"),
                action_type=action.get("action_type", "unknown"),
                action_params=action.get("action_params"),
                reasoning=action.get("reasoning"),
                predicted_savings_eur=action.get("predicted_savings_eur"),
                predicted_savings_kwh=action.get("predicted_savings_kwh"),
                confidence_score=action.get("confidence_score"),
                status=action.get("status", "pending"),
                executed_at=(
                    datetime.fromisoformat(action["executed_at"])
                    if action.get("executed_at")
                    else None
                ),
                result=action.get("result"),
                error_message=action.get("error_message"),
                comfort_impact=action.get("comfort_impact"),
            )
            self.db.add(record)

        try:
            self.db.commit()
            logger.info(
                "autopilot.actions_saved",
                extra={"site_id": site_id, "count": len(actions)},
            )
        except Exception as exc:
            self.db.rollback()
            logger.exception(
                "autopilot.actions_save_failed",
                extra={"site_id": site_id, "error": str(exc)},
            )
