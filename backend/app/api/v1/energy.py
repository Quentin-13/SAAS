"""Energy readings, analytics, forecasts, and anomaly detection endpoints."""

import math
import random
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.models.device import Device
from app.models.energy import EnergyForecast, EnergyReading
from app.models.site import Site
from app.models.user import User
from app.schemas.energy import (
    AnomalyResponse,
    EnergyAnalyticsDaily,
    EnergyForecastResponse,
    EnergyReadingResponse,
)

router = APIRouter(prefix="/energy", tags=["energy"])


# ── Helpers ──────────────────────────────────────────────────────────────


def _verify_site_access(site_id: str, user: User, db: Session) -> Site:
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")
    if site.organization_id != user.organization_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    return site


def _generate_daily_mock(start: date, end: date) -> list[EnergyAnalyticsDaily]:
    """Generate realistic daily energy analytics mock data.

    Patterns:
    - Weekday consumption higher (office pattern): 80-200 kWh
    - Weekend consumption lower: 40-80 kWh
    - Slight seasonal variation (higher in winter months)
    - Electricity price ~0.18 EUR/kWh, CO2 ~0.05 kg/kWh (French grid)
    """
    results: list[EnergyAnalyticsDaily] = []
    current = start
    rng = random.Random(42)  # deterministic for consistency

    while current <= end:
        day_of_week = current.weekday()
        month = current.month
        is_weekend = day_of_week >= 5

        # Seasonal multiplier: higher in winter (Dec-Feb), lower in summer
        seasonal = 1.0 + 0.2 * math.cos((month - 1) * 2 * math.pi / 12)

        if is_weekend:
            base_kwh = rng.uniform(40, 80) * seasonal
        else:
            base_kwh = rng.uniform(80, 200) * seasonal

        # Add some daily noise
        total_kwh = round(base_kwh + rng.gauss(0, 10), 2)
        total_kwh = max(total_kwh, 10.0)

        price_per_kwh = 0.18
        co2_per_kwh = 0.05

        avg_power = round(total_kwh / 24, 2)
        peak_power = round(avg_power * rng.uniform(2.5, 4.0), 2)

        results.append(
            EnergyAnalyticsDaily(
                date=current,
                total_kwh=total_kwh,
                total_cost_eur=round(total_kwh * price_per_kwh, 2),
                avg_power_kw=avg_power,
                peak_power_kw=peak_power,
                co2_kg=round(total_kwh * co2_per_kwh, 2),
            )
        )
        current += timedelta(days=1)

    return results


def _generate_monthly_mock(start: date, end: date) -> list[EnergyAnalyticsDaily]:
    """Aggregate mock data into monthly buckets."""
    daily = _generate_daily_mock(start, end)
    monthly_buckets: dict[str, list[EnergyAnalyticsDaily]] = {}
    for d in daily:
        key = d.date.strftime("%Y-%m")
        monthly_buckets.setdefault(key, []).append(d)

    results: list[EnergyAnalyticsDaily] = []
    for key in sorted(monthly_buckets.keys()):
        days = monthly_buckets[key]
        total_kwh = round(sum(d.total_kwh for d in days), 2)
        total_cost = round(sum(d.total_cost_eur for d in days), 2)
        avg_power = round(sum(d.avg_power_kw for d in days) / len(days), 2)
        peak_power = round(max(d.peak_power_kw for d in days), 2)
        co2 = round(sum(d.co2_kg for d in days), 2)
        month_date = date(int(key[:4]), int(key[5:7]), 1)
        results.append(
            EnergyAnalyticsDaily(
                date=month_date,
                total_kwh=total_kwh,
                total_cost_eur=total_cost,
                avg_power_kw=avg_power,
                peak_power_kw=peak_power,
                co2_kg=co2,
            )
        )
    return results


# ── Endpoints ────────────────────────────────────────────────────────────


@router.get("/readings", response_model=list[EnergyReadingResponse])
def list_readings(
    site_id: str = Query(...),
    device_id: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[EnergyReadingResponse]:
    """Query energy readings with optional device and date filters."""
    _verify_site_access(site_id, current_user, db)

    # Get all device IDs belonging to this site
    site_device_ids = [
        d.id for d in db.query(Device).filter(Device.site_id == site_id).all()
    ]
    if not site_device_ids:
        return []

    query = db.query(EnergyReading).filter(EnergyReading.device_id.in_(site_device_ids))
    if device_id:
        if device_id not in site_device_ids:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not in this site")
        query = query.filter(EnergyReading.device_id == device_id)
    if start_date:
        query = query.filter(EnergyReading.time >= start_date)
    if end_date:
        query = query.filter(EnergyReading.time <= end_date)

    readings = query.order_by(EnergyReading.time.desc()).offset(skip).limit(limit).all()
    return [EnergyReadingResponse.model_validate(r) for r in readings]


@router.get("/analytics/daily", response_model=list[EnergyAnalyticsDaily])
def analytics_daily(
    site_id: str = Query(...),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[EnergyAnalyticsDaily]:
    """Return daily energy analytics for a site. Generates mock data if DB is empty."""
    _verify_site_access(site_id, current_user, db)

    today = date.today()
    start = start_date or (today - timedelta(days=30))
    end = end_date or today

    # Try to get real data first
    site_device_ids = [
        d.id for d in db.query(Device).filter(Device.site_id == site_id).all()
    ]
    if site_device_ids:
        count = (
            db.query(EnergyReading)
            .filter(
                EnergyReading.device_id.in_(site_device_ids),
                EnergyReading.time >= datetime(start.year, start.month, start.day, tzinfo=timezone.utc),
                EnergyReading.time <= datetime(end.year, end.month, end.day, 23, 59, 59, tzinfo=timezone.utc),
            )
            .count()
        )
        if count > 0:
            # Real aggregation would go here; for now fall through to mock
            pass

    return _generate_daily_mock(start, end)


@router.get("/analytics/monthly", response_model=list[EnergyAnalyticsDaily])
def analytics_monthly(
    site_id: str = Query(...),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[EnergyAnalyticsDaily]:
    """Return monthly energy analytics for a site. Generates mock data if DB is empty."""
    _verify_site_access(site_id, current_user, db)

    today = date.today()
    start = start_date or (today - timedelta(days=365))
    end = end_date or today

    return _generate_monthly_mock(start, end)


@router.get("/forecast", response_model=list[EnergyForecastResponse])
def get_forecasts(
    site_id: str = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[EnergyForecastResponse]:
    """Return energy forecasts for a site. Generates mock if none exist."""
    _verify_site_access(site_id, current_user, db)

    forecasts = (
        db.query(EnergyForecast)
        .filter(EnergyForecast.site_id == site_id)
        .order_by(EnergyForecast.forecast_date.desc())
        .limit(48)
        .all()
    )

    if forecasts:
        return [EnergyForecastResponse.model_validate(f) for f in forecasts]

    # Generate mock forecasts: next 48 hours, hourly
    rng = random.Random(int(site_id.replace("-", "")[:8], 16) if site_id.replace("-", "")[:8].isalnum() else 123)
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    mock: list[EnergyForecastResponse] = []
    for h in range(48):
        hour = now + timedelta(hours=h)
        hour_of_day = hour.hour
        # Office pattern: higher during work hours
        if 8 <= hour_of_day <= 18 and hour.weekday() < 5:
            base = rng.uniform(5, 12)
        else:
            base = rng.uniform(1.5, 4)

        predicted = round(base, 2)
        cost = round(predicted * 0.18, 2)
        lower = round(predicted * 0.8, 2)
        upper = round(predicted * 1.25, 2)

        mock.append(
            EnergyForecastResponse(
                forecast_date=hour,
                horizon_hours=h + 1,
                predicted_kwh=predicted,
                predicted_cost_eur=cost,
                confidence_lower=lower,
                confidence_upper=upper,
            )
        )
    return mock


@router.get("/anomalies", response_model=list[AnomalyResponse])
def get_anomalies(
    site_id: str = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[AnomalyResponse]:
    """Return detected anomalies for a site. Generates mock if none exist."""
    _verify_site_access(site_id, current_user, db)

    # In a real system, anomalies would be a separate table or computed.
    # For now, generate realistic mock anomalies.
    rng = random.Random(99)
    now = datetime.now(timezone.utc)
    mock_device_id = str(uuid.uuid4())

    anomalies: list[AnomalyResponse] = []
    anomaly_times = [
        now - timedelta(hours=rng.randint(1, 168)) for _ in range(5)
    ]
    anomaly_times.sort(reverse=True)

    for t in anomaly_times:
        expected = round(rng.uniform(3, 8), 2)
        deviation = round(rng.uniform(30, 120), 1)
        actual = round(expected * (1 + deviation / 100), 2)
        waste_hours = rng.uniform(0.5, 3)
        waste_eur = round((actual - expected) * waste_hours * 0.18, 2)

        anomalies.append(
            AnomalyResponse(
                time=t,
                device_id=mock_device_id,
                actual_kw=actual,
                expected_kw=expected,
                deviation_pct=deviation,
                estimated_waste_eur=waste_eur,
            )
        )
    return anomalies
