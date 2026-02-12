"""Celery task for running the autopilot cycle."""
import logging
from datetime import datetime

from app.tasks.celery_app import celery_app
from app.database import SessionLocal

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.run_autopilot.run_autopilot_cycle", bind=True, max_retries=3)
def run_autopilot_cycle(self):
    """Execute autopilot for all enabled sites. Runs every 15 minutes."""
    logger.info("Starting autopilot cycle at %s", datetime.utcnow().isoformat())
    db = SessionLocal()
    try:
        from app.models.site import Site
        from app.services.autopilot.engine import AutopilotEngine

        sites = db.query(Site).filter(Site.autopilot_enabled.is_(True)).all()
        logger.info("Found %d sites with autopilot enabled", len(sites))

        total_actions = 0
        for site in sites:
            try:
                engine = AutopilotEngine(db)
                # Run synchronously in Celery context
                import asyncio
                loop = asyncio.new_event_loop()
                try:
                    actions = loop.run_until_complete(engine.run(str(site.id)))
                finally:
                    loop.close()
                action_count = len(actions) if actions else 0
                total_actions += action_count
                logger.info(
                    "Autopilot completed for site %s: %d actions",
                    site.id,
                    action_count,
                )
            except Exception as exc:
                logger.error(
                    "Autopilot failed for site %s: %s",
                    site.id,
                    str(exc),
                    exc_info=True,
                )

        logger.info("Autopilot cycle complete: %d total actions across %d sites", total_actions, len(sites))
        return {"sites_processed": len(sites), "total_actions": total_actions}

    except Exception as exc:
        logger.error("Autopilot cycle failed: %s", str(exc), exc_info=True)
        raise self.retry(exc=exc, countdown=60)
    finally:
        db.close()
