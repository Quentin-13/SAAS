"""
Data synchronisation Celery tasks.

These tasks run outside of the FastAPI request lifecycle, so they create
and close their own SQLAlchemy sessions via ``SessionLocal``.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_db_session():
    """Return a new synchronous SQLAlchemy session (caller must close)."""
    from app.database import SessionLocal
    return SessionLocal()


def _run_async(coro):
    """Run an async coroutine from synchronous Celery worker code."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------

@celery_app.task(bind=True, name="app.tasks.sync_data.sync_energy_data")
def sync_energy_data(self):
    """Sync the last 48 hours of consumption data for every active Linky device.

    Each device is processed independently so that a failure on one device
    does not prevent the others from being updated.
    """
    from app.models.device import Device
    from app.services.integrations.linky import LinkyClient

    db = _get_db_session()
    try:
        devices = (
            db.query(Device)
            .filter(
                Device.is_active.is_(True),
                Device.brand == "linky",
                Device.device_type == "meter",
            )
            .all()
        )

        logger.info("sync_energy_data: found %d active Linky device(s)", len(devices))

        success_count = 0
        error_count = 0

        for device in devices:
            try:
                _sync_single_linky_device(db, device)
                success_count += 1
            except Exception:
                error_count += 1
                logger.exception(
                    "sync_energy_data: failed to sync device %s (%s)",
                    device.id,
                    device.name,
                )
                db.rollback()

        logger.info(
            "sync_energy_data: completed -- %d succeeded, %d failed",
            success_count,
            error_count,
        )
        return {
            "total_devices": len(devices),
            "success": success_count,
            "errors": error_count,
        }
    finally:
        db.close()


def _sync_single_linky_device(db, device):
    """Fetch 48h of consumption for a single Linky device and persist readings."""
    from app.models.energy import EnergyReading
    from app.services.integrations.linky import LinkyClient

    client = LinkyClient()

    # Determine date range (last 48 h)
    now = datetime.now(tz=timezone.utc)
    start_date = (now - timedelta(hours=48)).strftime("%Y-%m-%d")
    end_date = now.strftime("%Y-%m-%d")

    # Extract credentials stored on the device
    creds = device.api_credentials or {}
    access_token = creds.get("access_token", "")
    usage_point_id = device.external_id or ""

    readings = _run_async(
        client.get_consumption(
            access_token=access_token,
            usage_point_id=usage_point_id,
            start=start_date,
            end=end_date,
        )
    )

    persisted = 0
    for r in readings:
        time_str = r.get("time")
        if not time_str:
            continue
        try:
            ts = datetime.fromisoformat(time_str)
        except (ValueError, TypeError):
            continue

        # Upsert: check if reading already exists
        existing = (
            db.query(EnergyReading)
            .filter(
                EnergyReading.device_id == device.id,
                EnergyReading.time == ts,
            )
            .first()
        )
        if existing:
            existing.power_kw = r.get("power_kw")
            existing.energy_kwh = r.get("energy_kwh")
        else:
            db.add(
                EnergyReading(
                    time=ts,
                    device_id=device.id,
                    power_kw=r.get("power_kw"),
                    energy_kwh=r.get("energy_kwh"),
                )
            )
        persisted += 1

    device.last_sync = datetime.now(tz=timezone.utc)
    db.commit()

    logger.info(
        "sync_energy_data: device %s -- %d readings synced",
        device.id,
        persisted,
    )


@celery_app.task(bind=True, name="app.tasks.sync_data.sync_device_states")
def sync_device_states(self):
    """Refresh the ``current_state`` of every active thermostat device.

    Each device is processed independently so that a failure on one device
    does not block the rest.
    """
    from app.models.device import Device

    db = _get_db_session()
    try:
        devices = (
            db.query(Device)
            .filter(
                Device.is_active.is_(True),
                Device.device_type == "thermostat",
            )
            .all()
        )

        logger.info(
            "sync_device_states: found %d active thermostat(s)", len(devices),
        )

        success_count = 0
        error_count = 0

        for device in devices:
            try:
                _refresh_thermostat_state(db, device)
                success_count += 1
            except Exception:
                error_count += 1
                logger.exception(
                    "sync_device_states: failed for device %s (%s / %s)",
                    device.id,
                    device.name,
                    device.brand,
                )
                db.rollback()

        logger.info(
            "sync_device_states: completed -- %d succeeded, %d failed",
            success_count,
            error_count,
        )
        return {
            "total_devices": len(devices),
            "success": success_count,
            "errors": error_count,
        }
    finally:
        db.close()


def _refresh_thermostat_state(db, device):
    """Query the appropriate vendor API and update ``device.current_state``.

    Supports Nest and Netatmo brands; other brands are skipped with a
    warning log message.
    """
    brand = (device.brand or "").lower()

    if brand == "nest":
        state = _fetch_nest_state(device)
    elif brand == "netatmo":
        state = _fetch_netatmo_state(device)
    else:
        logger.warning(
            "sync_device_states: unsupported thermostat brand '%s' for device %s",
            brand,
            device.id,
        )
        return

    device.current_state = state
    device.last_sync = datetime.now(tz=timezone.utc)
    db.commit()

    logger.info(
        "sync_device_states: device %s (%s) state updated",
        device.id,
        brand,
    )


def _fetch_nest_state(device) -> dict:
    """Fetch current state from Google Nest API (placeholder).

    In production this would use the Smart Device Management API.
    For now it returns a mock state dict.
    """
    return {
        "mode": "heat",
        "current_temperature": 20.5,
        "target_temperature": 21.0,
        "humidity": 45,
        "online": True,
    }


def _fetch_netatmo_state(device) -> dict:
    """Fetch current state from Netatmo API (placeholder).

    In production this would use the Netatmo Energy API.
    For now it returns a mock state dict.
    """
    return {
        "mode": "schedule",
        "current_temperature": 19.8,
        "target_temperature": 20.0,
        "battery_percent": 78,
        "online": True,
    }
