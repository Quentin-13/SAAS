"""SQLAlchemy models for the Energy Management SaaS platform.

Import all models here so that ``Base.metadata`` is fully populated when
Alembic (or any other tool) inspects it.
"""

from app.models.action import AutopilotAction
from app.models.device import Device
from app.models.energy import EnergyForecast, EnergyReading
from app.models.site import Site, Zone
from app.models.subscription import Subscription
from app.models.user import Organization, User

__all__ = [
    "AutopilotAction",
    "Device",
    "EnergyForecast",
    "EnergyReading",
    "Organization",
    "Site",
    "Subscription",
    "User",
    "Zone",
]
