"""Autopilot actions, savings, and configuration endpoints."""

import random
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.models.action import AutopilotAction
from app.models.site import Site, Zone
from app.models.user import User
from app.schemas.action import (
    ActionFeedbackRequest,
    AutopilotActionResponse,
    AutopilotConfigResponse,
    AutopilotConfigUpdate,
    SavingsResponse,
)
from app.schemas.site import ZoneResponse

router = APIRouter(prefix="/autopilot", tags=["autopilot"])


# ── Helpers ──────────────────────────────────────────────────────────────


def _verify_site_access(site_id: str, user: User, db: Session) -> Site:
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")
    if site.organization_id != user.organization_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    return site


def _zone_to_response(zone: Zone) -> ZoneResponse:
    now = datetime.now(timezone.utc)
    return ZoneResponse(
        id=zone.id,
        site_id=zone.site_id,
        name=zone.name,
        zone_type=zone.zone_type,
        surface_area=zone.surface_area,
        target_temp_min=zone.target_temp_min,
        target_temp_max=zone.target_temp_max,
        occupancy_schedule=zone.occupancy_schedule,
        created_at=now,
        updated_at=now,
    )


# ── Actions ──────────────────────────────────────────────────────────────


@router.get("/actions", response_model=list[AutopilotActionResponse])
def list_actions(
    site_id: str = Query(...),
    action_status: Optional[str] = Query(None, alias="status"),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[AutopilotActionResponse]:
    """List autopilot actions for a site with optional filters."""
    _verify_site_access(site_id, current_user, db)

    query = db.query(AutopilotAction).filter(AutopilotAction.site_id == site_id)
    if action_status:
        query = query.filter(AutopilotAction.status == action_status)
    if start_date:
        query = query.filter(AutopilotAction.created_at >= start_date)
    if end_date:
        query = query.filter(AutopilotAction.created_at <= end_date)

    actions = query.order_by(AutopilotAction.created_at.desc()).offset(skip).limit(limit).all()
    return [AutopilotActionResponse.model_validate(a) for a in actions]


@router.get("/actions/{action_id}", response_model=AutopilotActionResponse)
def get_action(
    action_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> AutopilotActionResponse:
    """Get details of a single autopilot action."""
    action = db.query(AutopilotAction).filter(AutopilotAction.id == action_id).first()
    if not action:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Action not found")
    _verify_site_access(action.site_id, current_user, db)
    return AutopilotActionResponse.model_validate(action)


@router.post("/actions/{action_id}/feedback", response_model=AutopilotActionResponse)
def submit_feedback(
    action_id: str,
    payload: ActionFeedbackRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> AutopilotActionResponse:
    """Submit user feedback (positive/neutral/negative) for an autopilot action."""
    action = db.query(AutopilotAction).filter(AutopilotAction.id == action_id).first()
    if not action:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Action not found")
    _verify_site_access(action.site_id, current_user, db)

    action.user_feedback = payload.feedback.value
    db.commit()
    db.refresh(action)
    return AutopilotActionResponse.model_validate(action)


# ── Savings ──────────────────────────────────────────────────────────────


@router.get("/savings", response_model=SavingsResponse)
def get_savings(
    site_id: str = Query(...),
    period: str = Query("last_30_days", regex="^(last_7_days|last_30_days|last_90_days|last_12_months)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> SavingsResponse:
    """Calculate energy savings for a site. Returns mock data if no real data exists."""
    _verify_site_access(site_id, current_user, db)

    # Attempt to calculate from real actions
    period_days = {"last_7_days": 7, "last_30_days": 30, "last_90_days": 90, "last_12_months": 365}
    days = period_days.get(period, 30)
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    actions = (
        db.query(AutopilotAction)
        .filter(
            AutopilotAction.site_id == site_id,
            AutopilotAction.status == "executed",
            AutopilotAction.created_at >= cutoff,
        )
        .all()
    )

    if actions:
        saved_kwh = sum(a.actual_savings_kwh or a.predicted_savings_kwh or 0 for a in actions)
        saved_eur = sum(a.actual_savings_eur or a.predicted_savings_eur or 0 for a in actions)
        # Estimate baseline as saved + average daily consumption * days
        baseline_kwh = saved_kwh + (days * 120)  # ~120 kWh/day typical office
        actual_kwh = baseline_kwh - saved_kwh
    else:
        # Mock realistic savings
        rng = random.Random(hash(site_id) % 10000)
        daily_consumption = rng.uniform(80, 180)
        savings_pct = rng.uniform(0.15, 0.25)
        baseline_kwh = round(daily_consumption * days, 2)
        saved_kwh = round(baseline_kwh * savings_pct, 2)
        actual_kwh = round(baseline_kwh - saved_kwh, 2)
        saved_eur = round(saved_kwh * 0.18, 2)

    saved_pct = round((saved_kwh / baseline_kwh) * 100, 1) if baseline_kwh > 0 else 0.0
    co2_avoided = round(saved_kwh * 0.05, 2)

    return SavingsResponse(
        period=period,
        baseline_kwh=round(baseline_kwh, 2),
        actual_kwh=round(actual_kwh, 2),
        saved_kwh=round(saved_kwh, 2),
        saved_eur=round(saved_eur, 2),
        saved_pct=saved_pct,
        co2_avoided_kg=co2_avoided,
    )


# ── Config ───────────────────────────────────────────────────────────────


@router.get("/config", response_model=AutopilotConfigResponse)
def get_config(
    site_id: str = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> AutopilotConfigResponse:
    """Get autopilot configuration for a site (zones with temp constraints)."""
    site = _verify_site_access(site_id, current_user, db)
    zones = db.query(Zone).filter(Zone.site_id == site_id).all()

    return AutopilotConfigResponse(
        site_id=site.id,
        autopilot_enabled=site.autopilot_enabled,
        zones=[_zone_to_response(z) for z in zones],
    )


@router.patch("/config", response_model=AutopilotConfigResponse)
def update_config(
    site_id: str = Query(...),
    payload: AutopilotConfigUpdate = ...,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> AutopilotConfigResponse:
    """Update autopilot configuration: toggle autopilot, update zone temp limits and schedules."""
    site = _verify_site_access(site_id, current_user, db)

    if payload.autopilot_enabled is not None:
        site.autopilot_enabled = payload.autopilot_enabled

    if payload.zones is not None:
        # Update existing zones or create new ones
        existing_zones = {z.name: z for z in db.query(Zone).filter(Zone.site_id == site_id).all()}
        for zone_data in payload.zones:
            if zone_data.name in existing_zones:
                zone = existing_zones[zone_data.name]
                zone.zone_type = zone_data.zone_type
                zone.surface_area = zone_data.surface_area
                zone.target_temp_min = zone_data.target_temp_min
                zone.target_temp_max = zone_data.target_temp_max
                zone.occupancy_schedule = zone_data.occupancy_schedule
            else:
                new_zone = Zone(
                    site_id=site_id,
                    name=zone_data.name,
                    zone_type=zone_data.zone_type,
                    surface_area=zone_data.surface_area,
                    target_temp_min=zone_data.target_temp_min,
                    target_temp_max=zone_data.target_temp_max,
                    occupancy_schedule=zone_data.occupancy_schedule,
                )
                db.add(new_zone)

    db.commit()
    db.refresh(site)
    zones = db.query(Zone).filter(Zone.site_id == site_id).all()

    return AutopilotConfigResponse(
        site_id=site.id,
        autopilot_enabled=site.autopilot_enabled,
        zones=[_zone_to_response(z) for z in zones],
    )
