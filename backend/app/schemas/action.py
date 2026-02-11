from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict

from app.schemas.energy import EnergyAnalyticsDaily
from app.schemas.site import ZoneCreate, ZoneResponse


class FeedbackType(str, Enum):
    positive = "positive"
    neutral = "neutral"
    negative = "negative"


class AutopilotActionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    site_id: str
    device_id: str
    action_type: str
    action_params: Dict[str, Any]
    reasoning: Optional[str] = None
    predicted_savings_eur: Optional[float] = None
    predicted_savings_kwh: Optional[float] = None
    confidence_score: Optional[float] = None
    status: str
    executed_at: Optional[datetime] = None
    actual_savings_eur: Optional[float] = None
    comfort_impact: Optional[str] = None
    user_feedback: Optional[str] = None
    created_at: datetime


class ActionFeedbackRequest(BaseModel):
    feedback: FeedbackType


class AutopilotConfigResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    site_id: str
    autopilot_enabled: bool
    zones: List[ZoneResponse]


class AutopilotConfigUpdate(BaseModel):
    autopilot_enabled: Optional[bool] = None
    zones: Optional[List[ZoneCreate]] = None


class DashboardOverview(BaseModel):
    total_savings_eur: float
    total_savings_pct: float
    total_kwh_saved: float
    co2_avoided_kg: float
    actions_count: int
    active_sites: int
    active_devices: int
    daily_consumption: List[EnergyAnalyticsDaily]
    recent_actions: List[AutopilotActionResponse]


class SavingsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    period: str
    baseline_kwh: float
    actual_kwh: float
    saved_kwh: float
    saved_eur: float
    saved_pct: float
    co2_avoided_kg: float
