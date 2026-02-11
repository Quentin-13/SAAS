from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class EnergyReadingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    time: datetime
    device_id: str
    power_kw: Optional[float] = None
    energy_kwh: Optional[float] = None
    cost_eur: Optional[float] = None
    temperature: Optional[float] = None
    outdoor_temp: Optional[float] = None
    is_occupied: Optional[bool] = None


class EnergyAnalyticsDaily(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    date: date
    total_kwh: float
    total_cost_eur: float
    avg_power_kw: float
    peak_power_kw: float
    co2_kg: float


class EnergyForecastResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    forecast_date: datetime
    horizon_hours: int
    predicted_kwh: float
    predicted_cost_eur: float
    confidence_lower: float
    confidence_upper: float


class AnomalyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    time: datetime
    device_id: str
    actual_kw: float
    expected_kw: float
    deviation_pct: float
    estimated_waste_eur: float
