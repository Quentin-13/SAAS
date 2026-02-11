"""Device management and integration sync endpoints."""

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.models.device import Device
from app.models.site import Site
from app.models.user import User
from app.schemas.device import (
    DeviceControlRequest,
    DeviceCreate,
    DeviceResponse,
    DeviceUpdate,
)

router = APIRouter(prefix="/devices", tags=["devices"])


# ── Helpers ──────────────────────────────────────────────────────────────


def _verify_site_ownership(site_id: str, user: User, db: Session) -> Site:
    """Ensure the site belongs to the current user's organization."""
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")
    if site.organization_id != user.organization_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this site")
    return site


def _get_device_or_404(device_id: str, user: User, db: Session) -> Device:
    """Fetch a device and verify ownership through its parent site."""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    _verify_site_ownership(device.site_id, user, db)
    return device


def _device_to_response(device: Device) -> DeviceResponse:
    return DeviceResponse(
        id=device.id,
        site_id=device.site_id,
        zone_id=device.zone_id,
        device_type=device.device_type,
        brand=device.brand or "generic",
        model=device.model,
        external_id=device.external_id,
        name=device.name or "Unnamed",
        is_controllable=device.is_controllable,
        capabilities=device.capabilities,
        created_at=device.created_at,
        updated_at=device.created_at,  # Device model has no updated_at
    )


# ── CRUD ─────────────────────────────────────────────────────────────────


@router.get("/", response_model=list[DeviceResponse])
def list_devices(
    site_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[DeviceResponse]:
    """List devices, optionally filtered by site_id."""
    query = db.query(Device)
    if site_id:
        _verify_site_ownership(site_id, current_user, db)
        query = query.filter(Device.site_id == site_id)
    else:
        # Only show devices from user's org sites
        org_site_ids = [
            s.id
            for s in db.query(Site)
            .filter(Site.organization_id == current_user.organization_id)
            .all()
        ]
        query = query.filter(Device.site_id.in_(org_site_ids))
    devices = query.offset(skip).limit(limit).all()
    return [_device_to_response(d) for d in devices]


@router.post("/", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
def create_device(
    payload: DeviceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> DeviceResponse:
    """Register a new device under a site."""
    _verify_site_ownership(payload.site_id, current_user, db)
    device = Device(
        site_id=payload.site_id,
        zone_id=payload.zone_id,
        device_type=payload.device_type,
        brand=payload.brand,
        model=payload.model,
        external_id=payload.external_id,
        name=payload.name,
        is_controllable=payload.is_controllable,
        capabilities=payload.capabilities,
    )
    db.add(device)
    db.commit()
    db.refresh(device)
    return _device_to_response(device)


@router.get("/{device_id}", response_model=DeviceResponse)
def get_device(
    device_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> DeviceResponse:
    """Get a single device by ID."""
    device = _get_device_or_404(device_id, current_user, db)
    return _device_to_response(device)


@router.patch("/{device_id}", response_model=DeviceResponse)
def update_device(
    device_id: str,
    payload: DeviceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> DeviceResponse:
    """Update device fields."""
    device = _get_device_or_404(device_id, current_user, db)
    update_data = payload.model_dump(exclude_unset=True)
    if "site_id" in update_data:
        _verify_site_ownership(update_data["site_id"], current_user, db)
    for field, value in update_data.items():
        setattr(device, field, value)
    db.commit()
    db.refresh(device)
    return _device_to_response(device)


@router.delete("/{device_id}")
def delete_device(
    device_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """Delete a device."""
    device = _get_device_or_404(device_id, current_user, db)
    db.delete(device)
    db.commit()
    return {"ok": True}


# ── Device control ───────────────────────────────────────────────────────


@router.post("/{device_id}/control")
def control_device(
    device_id: str,
    payload: DeviceControlRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """Send a control command to a device via its brand integration client."""
    device = _get_device_or_404(device_id, current_user, db)
    if not device.is_controllable:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Device is not controllable",
        )

    # Dispatch based on brand (placeholder integration)
    brand = (device.brand or "generic").lower()
    if brand == "nest":
        result = {"status": "ok", "brand": "nest", "message": f"Nest command '{payload.command}' sent"}
    elif brand == "netatmo":
        result = {"status": "ok", "brand": "netatmo", "message": f"Netatmo command '{payload.command}' sent"}
    elif brand == "tado":
        result = {"status": "ok", "brand": "tado", "message": f"Tado command '{payload.command}' sent"}
    else:
        result = {"status": "ok", "brand": brand, "message": f"Generic command '{payload.command}' sent"}

    # Persist new state
    device.current_state = {
        "last_command": payload.command,
        "params": payload.params,
        "sent_at": datetime.now(timezone.utc).isoformat(),
    }
    db.commit()
    return result


# ── Sync placeholders ───────────────────────────────────────────────────


@router.post("/sync/nest", response_model=list[DeviceResponse])
def sync_nest(
    current_user: User = Depends(get_current_active_user),
) -> list[DeviceResponse]:
    """Placeholder: sync devices from Google Nest account."""
    now = datetime.now(timezone.utc)
    return [
        DeviceResponse(
            id=str(uuid.uuid4()),
            site_id="mock-site-id",
            device_type="thermostat",
            brand="nest",
            name="Nest Learning Thermostat",
            is_controllable=True,
            capabilities={"temperature": True, "humidity": True, "eco_mode": True},
            created_at=now,
            updated_at=now,
        ),
        DeviceResponse(
            id=str(uuid.uuid4()),
            site_id="mock-site-id",
            device_type="thermostat",
            brand="nest",
            name="Nest Thermostat E",
            is_controllable=True,
            capabilities={"temperature": True, "eco_mode": True},
            created_at=now,
            updated_at=now,
        ),
    ]


@router.post("/sync/netatmo", response_model=list[DeviceResponse])
def sync_netatmo(
    current_user: User = Depends(get_current_active_user),
) -> list[DeviceResponse]:
    """Placeholder: sync devices from Netatmo account."""
    now = datetime.now(timezone.utc)
    return [
        DeviceResponse(
            id=str(uuid.uuid4()),
            site_id="mock-site-id",
            device_type="thermostat",
            brand="netatmo",
            name="Netatmo Smart Thermostat",
            is_controllable=True,
            capabilities={"temperature": True, "humidity": True, "co2": True},
            created_at=now,
            updated_at=now,
        ),
    ]


@router.post("/sync/linky", response_model=list[DeviceResponse])
def sync_linky(
    current_user: User = Depends(get_current_active_user),
) -> list[DeviceResponse]:
    """Placeholder: sync Linky smart meter data via Enedis API."""
    now = datetime.now(timezone.utc)
    return [
        DeviceResponse(
            id=str(uuid.uuid4()),
            site_id="mock-site-id",
            device_type="meter",
            brand="linky",
            name="Compteur Linky",
            is_controllable=False,
            capabilities={"consumption": True, "peak_off_peak": True},
            created_at=now,
            updated_at=now,
        ),
    ]
