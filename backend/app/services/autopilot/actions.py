"""Action execution layer for the Autopilot engine.

Responsible for dispatching validated actions to the appropriate device
integration client (Nest, Netatmo, etc.) and returning an updated action
dict with execution results.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.services.integrations.base import IntegrationError

logger = logging.getLogger(__name__)


class ActionExecutor:
    """Execute autopilot actions by calling the appropriate integration API.

    Parameters
    ----------
    db:
        Active SQLAlchemy session (kept for potential future use, e.g.
        credential look-ups or audit logging at execution time).
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    # ── Public API ───────────────────────────────────────────────────────

    async def execute(self, action: dict, device_data: dict) -> dict:
        """Execute a single action on the target device.

        The method selects an integration client based on the device's
        ``brand`` field and calls the relevant API method.

        Parameters
        ----------
        action:
            Action dict containing at least ``action_type`` and
            ``action_params``.
        device_data:
            Device dict (or serialised Device model) with ``brand``,
            ``external_id``, ``api_credentials``, and other device metadata.

        Returns
        -------
        dict
            The *action* dict updated with:
            - ``status`` set to ``"executed"`` or ``"failed"``.
            - ``executed_at`` ISO-formatted timestamp.
            - ``result`` (on success) or ``error_message`` (on failure).
        """
        brand = (device_data.get("brand") or "generic").lower()
        device_id = device_data.get("id", "unknown")

        logger.info(
            "action_executor.start",
            extra={
                "device_id": device_id,
                "brand": brand,
                "action_type": action.get("action_type"),
            },
        )

        try:
            if brand == "nest":
                result = await self._execute_nest(action, device_data)
            elif brand == "netatmo":
                result = await self._execute_netatmo(action, device_data)
            else:
                result = await self._execute_generic(action, device_data)

            action["status"] = "executed"
            action["executed_at"] = datetime.now(timezone.utc).isoformat()
            action["result"] = result

            logger.info(
                "action_executor.success",
                extra={
                    "device_id": device_id,
                    "brand": brand,
                    "action_type": action.get("action_type"),
                },
            )

        except IntegrationError as exc:
            action["status"] = "failed"
            action["executed_at"] = datetime.now(timezone.utc).isoformat()
            action["error_message"] = str(exc)

            logger.error(
                "action_executor.integration_error",
                extra={
                    "device_id": device_id,
                    "brand": brand,
                    "error": str(exc),
                },
            )

        except Exception as exc:
            action["status"] = "failed"
            action["executed_at"] = datetime.now(timezone.utc).isoformat()
            action["error_message"] = f"Unexpected error: {exc}"

            logger.exception(
                "action_executor.unexpected_error",
                extra={
                    "device_id": device_id,
                    "brand": brand,
                },
            )

        return action

    # ── Brand-specific handlers ──────────────────────────────────────────

    async def _execute_nest(self, action: dict, device_data: dict) -> dict:
        """Call the Nest API to execute *action*.

        Supports ``temperature_adjustment`` (set_temperature) and
        ``mode_change`` (set_mode) action types.
        """
        from app.services.integrations.nest import NestClient

        client = NestClient()
        params = action.get("action_params") or {}
        external_id = device_data.get("external_id", "")
        credentials = device_data.get("api_credentials") or {}

        action_type = action.get("action_type")

        if action_type == "temperature_adjustment":
            target_temp = params.get("target_temperature")
            logger.debug(
                "action_executor.nest.set_temperature",
                extra={
                    "external_id": external_id,
                    "target_temperature": target_temp,
                },
            )
            result = await client.set_temperature(
                device_id=external_id,
                temperature=target_temp,
                credentials=credentials,
            )
        elif action_type == "mode_change":
            mode = params.get("mode")
            logger.debug(
                "action_executor.nest.set_mode",
                extra={
                    "external_id": external_id,
                    "mode": mode,
                },
            )
            result = await client.set_mode(
                device_id=external_id,
                mode=mode,
                credentials=credentials,
            )
        else:
            logger.warning(
                "action_executor.nest.unsupported_action",
                extra={"action_type": action_type},
            )
            result = {"status": "skipped", "reason": f"Unsupported action type: {action_type}"}

        return result

    async def _execute_netatmo(self, action: dict, device_data: dict) -> dict:
        """Call the Netatmo API to execute *action*.

        Uses ``set_thermpoint`` for temperature adjustments.
        """
        from app.services.integrations.netatmo import NetatmoClient

        client = NetatmoClient()
        params = action.get("action_params") or {}
        external_id = device_data.get("external_id", "")
        credentials = device_data.get("api_credentials") or {}

        action_type = action.get("action_type")

        if action_type == "temperature_adjustment":
            target_temp = params.get("target_temperature")
            logger.debug(
                "action_executor.netatmo.set_thermpoint",
                extra={
                    "external_id": external_id,
                    "target_temperature": target_temp,
                },
            )
            result = await client.set_thermpoint(
                device_id=external_id,
                temperature=target_temp,
                credentials=credentials,
            )
        else:
            logger.warning(
                "action_executor.netatmo.unsupported_action",
                extra={"action_type": action_type},
            )
            result = {"status": "skipped", "reason": f"Unsupported action type: {action_type}"}

        return result

    async def _execute_generic(self, action: dict, device_data: dict) -> dict:
        """Handle actions for generic / manual devices.

        No real API call is made; the action is logged and acknowledged.
        """
        logger.info(
            "action_executor.generic.log_only",
            extra={
                "device_id": device_data.get("id"),
                "action_type": action.get("action_type"),
                "action_params": action.get("action_params"),
            },
        )
        return {
            "status": "logged",
            "reason": "Generic/manual device — action recorded but not dispatched.",
        }
