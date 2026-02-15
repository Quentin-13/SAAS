"""Energy Autopilot API - Main FastAPI application."""
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncGenerator

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

# Configure structured logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan events."""
    # Startup
    logger.info("Starting %s v%s", settings.APP_NAME, settings.APP_VERSION)

    # Auto-create tables and seed demo data
    try:
        from app.database import engine, Base, SessionLocal
        import app.models  # noqa: F401 — ensure all models are registered
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created/verified")

        # Apply schema migrations for columns added after initial create_all
        from sqlalchemy import text, inspect as sa_inspect
        with engine.connect() as conn:
            inspector = sa_inspect(engine)

            # Add 'role' column to users if missing
            user_cols = [c["name"] for c in inspector.get_columns("users")]
            if "role" not in user_cols:
                conn.execute(text(
                    "ALTER TABLE users ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'user'"
                ))
                conn.execute(text(
                    "UPDATE users SET role = 'admin' WHERE is_superuser = true"
                ))
                conn.commit()
                logger.info("Added 'role' column to users table")

            # Add stripe fields to subscriptions if missing
            sub_cols = [c["name"] for c in inspector.get_columns("subscriptions")]
            if "stripe_customer_id" not in sub_cols:
                conn.execute(text(
                    "ALTER TABLE subscriptions ADD COLUMN stripe_customer_id VARCHAR(255)"
                ))
                conn.commit()
                logger.info("Added 'stripe_customer_id' column to subscriptions table")
            if "stripe_subscription_id" not in sub_cols:
                conn.execute(text(
                    "ALTER TABLE subscriptions ADD COLUMN stripe_subscription_id VARCHAR(255)"
                ))
                conn.commit()
                logger.info("Added 'stripe_subscription_id' column to subscriptions table")

        # Auto-seed or refresh demo data
        try:
            from seed_data import seed
            seed()
            logger.info("Seed check completed successfully")
        except Exception as e:
            logger.warning("Could not check/seed database: %s", e)
    except Exception as e:
        logger.warning("Could not initialize database: %s", e)

    # Initialize Sentry if configured
    if settings.SENTRY_DSN:
        try:
            import sentry_sdk
            from sentry_sdk.integrations.fastapi import FastApiIntegration

            sentry_sdk.init(
                dsn=settings.SENTRY_DSN,
                integrations=[FastApiIntegration()],
                traces_sample_rate=0.1,
            )
            logger.info("Sentry initialized")
        except ImportError:
            logger.warning("sentry-sdk not installed, skipping Sentry init")

    yield

    # Shutdown
    logger.info("Shutting down %s", settings.APP_NAME)


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Plateforme de gestion énergétique prédictive avec autopilot IA",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
from app.api.v1.auth import router as auth_router
from app.api.v1.sites import router as sites_router
from app.api.v1.devices import router as devices_router
from app.api.v1.energy import router as energy_router
from app.api.v1.autopilot import router as autopilot_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.admin import router as admin_router

app.include_router(auth_router, prefix="/api/v1")
app.include_router(sites_router, prefix="/api/v1")
app.include_router(devices_router, prefix="/api/v1")
app.include_router(energy_router, prefix="/api/v1")
app.include_router(autopilot_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")


@app.get("/health", tags=["system"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/readiness", tags=["system"])
async def readiness_check():
    """Readiness check - verifies DB and Redis connections."""
    checks = {"database": "unknown", "redis": "unknown"}

    # Check database
    try:
        from app.database import SessionLocal
        db = SessionLocal()
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        db.close()
        checks["database"] = "connected"
    except Exception as e:
        checks["database"] = f"error: {str(e)}"

    # Check Redis
    try:
        import redis
        r = redis.from_url(settings.REDIS_URL)
        r.ping()
        checks["redis"] = "connected"
    except Exception as e:
        checks["redis"] = f"error: {str(e)}"

    all_healthy = all(v == "connected" for v in checks.values())
    return {
        "status": "ready" if all_healthy else "degraded",
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat(),
    }


# WebSocket connections manager
class ConnectionManager:
    """Manages WebSocket connections for real-time dashboard updates."""

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("WebSocket connected. Total: %d", len(self.active_connections))

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info("WebSocket disconnected. Total: %d", len(self.active_connections))

    async def broadcast(self, message: dict):
        """Send message to all connected clients."""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
        for conn in disconnected:
            self.active_connections.remove(conn)


manager = ConnectionManager()


@app.websocket("/ws/dashboard")
async def websocket_dashboard(websocket: WebSocket):
    """WebSocket endpoint for real-time dashboard updates."""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Echo back with timestamp for heartbeat
            await websocket.send_json({
                "type": "heartbeat",
                "timestamp": datetime.utcnow().isoformat(),
                "received": data,
            })
    except WebSocketDisconnect:
        manager.disconnect(websocket)
