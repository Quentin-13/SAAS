"""Celery tasks for analytics calculations and model training."""
import logging
from datetime import datetime, timedelta

from app.tasks.celery_app import celery_app
from app.database import SessionLocal

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.analytics.calculate_daily_analytics", bind=True, max_retries=3)
def calculate_daily_analytics(self):
    """Calculate yesterday's daily analytics for all active sites. Runs daily at 00:30."""
    logger.info("Starting daily analytics calculation")
    db = SessionLocal()
    try:
        from app.models.site import Site
        from app.models.energy import EnergyReading
        from sqlalchemy import func

        sites = db.query(Site).filter(Site.autopilot_enabled.is_(True)).all()
        yesterday = datetime.utcnow().date() - timedelta(days=1)
        yesterday_start = datetime.combine(yesterday, datetime.min.time())
        yesterday_end = datetime.combine(yesterday, datetime.max.time())

        for site in sites:
            try:
                device_ids = [str(d.id) for d in site.devices]
                if not device_ids:
                    continue

                result = (
                    db.query(
                        func.sum(EnergyReading.energy_kwh).label("total_kwh"),
                        func.sum(EnergyReading.cost_eur).label("total_cost"),
                        func.avg(EnergyReading.power_kw).label("avg_power"),
                        func.max(EnergyReading.power_kw).label("peak_power"),
                    )
                    .filter(
                        EnergyReading.device_id.in_(device_ids),
                        EnergyReading.time >= yesterday_start,
                        EnergyReading.time <= yesterday_end,
                    )
                    .first()
                )

                if result and result.total_kwh:
                    logger.info(
                        "Daily analytics for site %s: %.1f kWh, %.2f EUR",
                        site.id,
                        result.total_kwh or 0,
                        result.total_cost or 0,
                    )

            except Exception as exc:
                logger.error("Analytics failed for site %s: %s", site.id, str(exc))

        return {"sites_processed": len(sites)}

    except Exception as exc:
        logger.error("Daily analytics failed: %s", str(exc), exc_info=True)
        raise self.retry(exc=exc, countdown=120)
    finally:
        db.close()


@celery_app.task(name="app.tasks.analytics.train_forecasting_models", bind=True, max_retries=2)
def train_forecasting_models(self):
    """Re-train Prophet forecasting models. Runs weekly on Sundays."""
    logger.info("Starting weekly model training")
    db = SessionLocal()
    try:
        from app.models.site import Site
        from app.models.energy import EnergyReading, EnergyForecast
        from app.services.ml.forecasting import EnergyForecaster

        sites = db.query(Site).filter(Site.autopilot_enabled.is_(True)).all()
        ninety_days_ago = datetime.utcnow() - timedelta(days=90)

        for site in sites:
            try:
                device_ids = [str(d.id) for d in site.devices]
                if not device_ids:
                    continue

                readings = (
                    db.query(EnergyReading)
                    .filter(
                        EnergyReading.device_id.in_(device_ids),
                        EnergyReading.time >= ninety_days_ago,
                    )
                    .all()
                )

                if len(readings) < 100:
                    logger.info("Insufficient data for site %s (%d readings)", site.id, len(readings))
                    continue

                historical = [
                    {
                        "time": r.time,
                        "energy_kwh": r.energy_kwh or 0,
                        "outdoor_temp": r.outdoor_temp or 12.0,
                        "is_occupied": r.is_occupied if r.is_occupied is not None else True,
                    }
                    for r in readings
                ]

                forecaster = EnergyForecaster(str(site.id))
                forecaster.train(historical)
                logger.info("Model trained for site %s with %d data points", site.id, len(readings))

            except Exception as exc:
                logger.error("Training failed for site %s: %s", site.id, str(exc), exc_info=True)

        return {"sites_processed": len(sites)}

    except Exception as exc:
        logger.error("Model training failed: %s", str(exc), exc_info=True)
        raise self.retry(exc=exc, countdown=300)
    finally:
        db.close()
