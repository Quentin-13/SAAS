"""Site and zone management endpoints."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.models.site import Site, Zone
from app.models.user import User
from app.schemas.site import (
    SiteCreate,
    SiteResponse,
    SiteUpdate,
    ZoneCreate,
    ZoneResponse,
)

router = APIRouter(prefix="/sites", tags=["sites"])


# ── Helpers ──────────────────────────────────────────────────────────────


def _get_site_or_404(site_id: str, user: User, db: Session) -> Site:
    """Fetch a site and verify the current user owns it (via org)."""
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")
    if site.organization_id != user.organization_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this site")
    return site


def _site_to_response(site: Site) -> SiteResponse:
    """Convert a Site ORM object to a SiteResponse, filling computed fields."""
    return SiteResponse(
        id=site.id,
        organization_id=site.organization_id or "",
        name=site.name,
        address=site.address,
        postal_code=site.postal_code,
        city=site.city,
        latitude=site.latitude,
        longitude=site.longitude,
        surface_area=site.surface_area,
        building_type=site.building_type,
        zones_count=len(site.zones) if site.zones else 0,
        devices_count=len(site.devices) if site.devices else 0,
        created_at=site.created_at,
        updated_at=site.created_at,  # Site model has no updated_at; use created_at
    )


def _zone_to_response(zone: Zone) -> ZoneResponse:
    """Convert a Zone ORM object to a ZoneResponse."""
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


# ── Site CRUD ────────────────────────────────────────────────────────────


@router.get("/", response_model=list[SiteResponse])
def list_sites(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[SiteResponse]:
    """List all sites belonging to the current user's organization."""
    query = db.query(Site).filter(Site.organization_id == current_user.organization_id)
    sites = query.offset(skip).limit(limit).all()
    return [_site_to_response(s) for s in sites]


@router.post("/", response_model=SiteResponse, status_code=status.HTTP_201_CREATED)
def create_site(
    payload: SiteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> SiteResponse:
    """Create a new site for the current user's organization."""
    site = Site(
        name=payload.name,
        address=payload.address,
        postal_code=payload.postal_code,
        city=payload.city,
        latitude=payload.latitude,
        longitude=payload.longitude,
        surface_area=payload.surface_area,
        building_type=payload.building_type.value if payload.building_type else None,
        owner_id=current_user.id,
        organization_id=current_user.organization_id,
    )
    db.add(site)
    db.commit()
    db.refresh(site)
    return _site_to_response(site)


@router.get("/{site_id}", response_model=SiteResponse)
def get_site(
    site_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> SiteResponse:
    """Get details of a single site."""
    site = _get_site_or_404(site_id, current_user, db)
    return _site_to_response(site)


@router.patch("/{site_id}", response_model=SiteResponse)
def update_site(
    site_id: str,
    payload: SiteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> SiteResponse:
    """Update an existing site."""
    site = _get_site_or_404(site_id, current_user, db)
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "building_type" and value is not None:
            value = value.value if hasattr(value, "value") else value
        setattr(site, field, value)
    db.commit()
    db.refresh(site)
    return _site_to_response(site)


@router.delete("/{site_id}")
def delete_site(
    site_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """Delete a site."""
    site = _get_site_or_404(site_id, current_user, db)
    db.delete(site)
    db.commit()
    return {"ok": True}


# ── Autopilot toggle ────────────────────────────────────────────────────


@router.post("/{site_id}/autopilot/enable", response_model=SiteResponse)
def enable_autopilot(
    site_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> SiteResponse:
    """Enable autopilot for a site."""
    site = _get_site_or_404(site_id, current_user, db)
    site.autopilot_enabled = True
    db.commit()
    db.refresh(site)
    return _site_to_response(site)


@router.post("/{site_id}/autopilot/disable", response_model=SiteResponse)
def disable_autopilot(
    site_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> SiteResponse:
    """Disable autopilot for a site."""
    site = _get_site_or_404(site_id, current_user, db)
    site.autopilot_enabled = False
    db.commit()
    db.refresh(site)
    return _site_to_response(site)


# ── Zones ────────────────────────────────────────────────────────────────


@router.post("/{site_id}/zones", response_model=ZoneResponse, status_code=status.HTTP_201_CREATED)
def create_zone(
    site_id: str,
    payload: ZoneCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ZoneResponse:
    """Create a zone inside a site."""
    _get_site_or_404(site_id, current_user, db)
    zone = Zone(
        site_id=site_id,
        name=payload.name,
        zone_type=payload.zone_type,
        surface_area=payload.surface_area,
        target_temp_min=payload.target_temp_min,
        target_temp_max=payload.target_temp_max,
        occupancy_schedule=payload.occupancy_schedule,
    )
    db.add(zone)
    db.commit()
    db.refresh(zone)
    return _zone_to_response(zone)


@router.get("/{site_id}/zones", response_model=list[ZoneResponse])
def list_zones(
    site_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[ZoneResponse]:
    """List all zones for a site."""
    _get_site_or_404(site_id, current_user, db)
    zones = db.query(Zone).filter(Zone.site_id == site_id).all()
    return [_zone_to_response(z) for z in zones]
