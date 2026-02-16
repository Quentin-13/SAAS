"""OAuth integration endpoints for Enedis, Netatmo, and Google Nest.

Each provider follows the same pattern:
  1. GET /auth/{provider}/start  → returns a redirect_url to the provider's consent page
  2. GET /auth/{provider}/callback → exchanges the authorization code for tokens,
     stores encrypted credentials, creates the device, and redirects to the frontend.

When MOCK_APIS is True (or client_id is empty), a mock token is returned and
the device is created immediately without hitting the real provider.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from urllib.parse import urlencode

import httpx
from cryptography.fernet import Fernet
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.config import settings
from app.models.device import Device

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["oauth-integrations"])

# ── Encryption helpers ───────────────────────────────────────────────────

_fernet = Fernet(settings.ENCRYPTION_KEY.encode() if isinstance(settings.ENCRYPTION_KEY, str) else settings.ENCRYPTION_KEY)


def _encrypt_credentials(data: dict) -> str:
    return _fernet.encrypt(json.dumps(data).encode()).decode()


def _decrypt_credentials(token: str) -> dict:
    return json.loads(_fernet.decrypt(token.encode()).decode())


# ── Helpers ──────────────────────────────────────────────────────────────

def _backend_base_url() -> str:
    """Return the public base URL of this backend (for OAuth callbacks)."""
    return settings.BASE_URL.rstrip("/")


def _frontend_url() -> str:
    return settings.FRONTEND_URL.rstrip("/")


def _is_mock(client_id: str) -> bool:
    """Return True when we should use mock mode for a given provider."""
    return settings.MOCK_APIS or not client_id


def _create_device(
    db: Session,
    *,
    site_id: str,
    device_name: str,
    device_type: str,
    brand: str,
    credentials: dict,
) -> Device:
    """Create a Device row with encrypted API credentials."""
    device = Device(
        id=str(uuid.uuid4()),
        site_id=site_id,
        name=device_name,
        device_type=device_type,
        brand=brand,
        is_controllable=brand != "linky",
        is_active=True,
        api_credentials={"encrypted": _encrypt_credentials(credentials)},
        last_sync=datetime.now(timezone.utc),
    )
    db.add(device)
    db.commit()
    db.refresh(device)
    logger.info("Device created: %s (%s/%s) for site %s", device.id, brand, device_type, site_id)
    return device


# ═════════════════════════════════════════════════════════════════════════
#  ENEDIS (Linky / Data Connect)
# ═════════════════════════════════════════════════════════════════════════

ENEDIS_AUTHORIZE_URL = "https://mon-compte-particulier.enedis.fr/dataconnect/v1/oauth2/authorize"
ENEDIS_TOKEN_URL = "https://gw.hml.api.enedis.fr/v1/oauth2/token"


@router.get("/enedis/start")
def enedis_start(
    site_id: str = Query(..., description="Site to attach the Linky meter to"),
    device_name: str = Query("Compteur Linky", description="Display name for the device"),
    db: Session = Depends(get_db),
):
    """Initiate the Enedis OAuth consent flow.

    - In mock mode: creates the device immediately and returns a redirect_url
      pointing to the frontend with ``?oauth=success``.
    - In real mode: returns a redirect_url to the Enedis consent page.
    """
    client_id = getattr(settings, "ENEDIS_CLIENT_ID", "") or settings.ENEDIS_API_KEY

    if _is_mock(client_id):
        mock_creds = {
            "access_token": f"mock-enedis-{uuid.uuid4().hex[:12]}",
            "refresh_token": f"mock-enedis-refresh-{uuid.uuid4().hex[:12]}",
            "token_type": "Bearer",
            "expires_in": 12600,
            "provider": "enedis",
        }
        _create_device(
            db,
            site_id=site_id,
            device_name=device_name,
            device_type="meter",
            brand="linky",
            credentials=mock_creds,
        )
        redirect = f"{_frontend_url()}/dashboard/sites/{site_id}?oauth=success&provider=enedis"
        return {"redirect_url": redirect, "mock": True}

    state = f"site_id:{site_id}|device_name:{device_name}"
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": f"{_backend_base_url()}/api/v1/auth/enedis/callback",
        "duration": "P3Y",
        "state": state,
    }
    redirect_url = f"{ENEDIS_AUTHORIZE_URL}?{urlencode(params)}"
    return {"redirect_url": redirect_url}


@router.get("/enedis/callback")
async def enedis_callback(
    code: str = Query(...),
    state: str = Query(""),
    db: Session = Depends(get_db),
):
    """Handle the Enedis OAuth callback: exchange code for tokens, create device."""
    # Parse state
    state_parts = dict(part.split(":", 1) for part in state.split("|") if ":" in part)
    site_id = state_parts.get("site_id", "")
    device_name = state_parts.get("device_name", "Compteur Linky")

    if not site_id:
        raise HTTPException(status_code=400, detail="Missing site_id in state")

    client_id = getattr(settings, "ENEDIS_CLIENT_ID", "") or settings.ENEDIS_API_KEY
    client_secret = getattr(settings, "ENEDIS_CLIENT_SECRET", "")

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            ENEDIS_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": f"{_backend_base_url()}/api/v1/auth/enedis/callback",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

    if resp.status_code != 200:
        logger.error("Enedis token exchange failed: %s %s", resp.status_code, resp.text)
        return RedirectResponse(
            f"{_frontend_url()}/dashboard/sites/{site_id}?oauth=error&provider=enedis"
        )

    tokens = resp.json()
    tokens["provider"] = "enedis"

    _create_device(
        db,
        site_id=site_id,
        device_name=device_name,
        device_type="meter",
        brand="linky",
        credentials=tokens,
    )

    return RedirectResponse(
        f"{_frontend_url()}/dashboard/sites/{site_id}?oauth=success&provider=enedis"
    )


# ═════════════════════════════════════════════════════════════════════════
#  NETATMO
# ═════════════════════════════════════════════════════════════════════════

NETATMO_AUTHORIZE_URL = "https://api.netatmo.com/oauth2/authorize"
NETATMO_TOKEN_URL = "https://api.netatmo.com/oauth2/token"


@router.get("/netatmo/start")
def netatmo_start(
    site_id: str = Query(...),
    device_name: str = Query("Thermostat Netatmo"),
    db: Session = Depends(get_db),
):
    """Initiate the Netatmo OAuth consent flow."""
    client_id = settings.NETATMO_CLIENT_ID

    if _is_mock(client_id):
        mock_creds = {
            "access_token": f"mock-netatmo-{uuid.uuid4().hex[:12]}",
            "refresh_token": f"mock-netatmo-refresh-{uuid.uuid4().hex[:12]}",
            "token_type": "Bearer",
            "expires_in": 10800,
            "provider": "netatmo",
        }
        _create_device(
            db,
            site_id=site_id,
            device_name=device_name,
            device_type="thermostat",
            brand="netatmo",
            credentials=mock_creds,
        )
        redirect = f"{_frontend_url()}/dashboard/sites/{site_id}?oauth=success&provider=netatmo"
        return {"redirect_url": redirect, "mock": True}

    state = f"site_id:{site_id}|device_name:{device_name}"
    params = {
        "client_id": client_id,
        "redirect_uri": f"{_backend_base_url()}/api/v1/auth/netatmo/callback",
        "scope": "read_thermostat write_thermostat",
        "state": state,
    }
    redirect_url = f"{NETATMO_AUTHORIZE_URL}?{urlencode(params)}"
    return {"redirect_url": redirect_url}


@router.get("/netatmo/callback")
async def netatmo_callback(
    code: str = Query(...),
    state: str = Query(""),
    db: Session = Depends(get_db),
):
    """Handle the Netatmo OAuth callback."""
    state_parts = dict(part.split(":", 1) for part in state.split("|") if ":" in part)
    site_id = state_parts.get("site_id", "")
    device_name = state_parts.get("device_name", "Thermostat Netatmo")

    if not site_id:
        raise HTTPException(status_code=400, detail="Missing site_id in state")

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            NETATMO_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": settings.NETATMO_CLIENT_ID,
                "client_secret": settings.NETATMO_CLIENT_SECRET,
                "redirect_uri": f"{_backend_base_url()}/api/v1/auth/netatmo/callback",
                "scope": "read_thermostat write_thermostat",
            },
        )

    if resp.status_code != 200:
        logger.error("Netatmo token exchange failed: %s %s", resp.status_code, resp.text)
        return RedirectResponse(
            f"{_frontend_url()}/dashboard/sites/{site_id}?oauth=error&provider=netatmo"
        )

    tokens = resp.json()
    tokens["provider"] = "netatmo"

    _create_device(
        db,
        site_id=site_id,
        device_name=device_name,
        device_type="thermostat",
        brand="netatmo",
        credentials=tokens,
    )

    return RedirectResponse(
        f"{_frontend_url()}/dashboard/sites/{site_id}?oauth=success&provider=netatmo"
    )


# ═════════════════════════════════════════════════════════════════════════
#  GOOGLE NEST (Smart Device Management API)
# ═════════════════════════════════════════════════════════════════════════

NEST_AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
NEST_TOKEN_URL = "https://oauth2.googleapis.com/token"
NEST_SDM_SCOPE = "https://www.googleapis.com/auth/sdm.service"


@router.get("/nest/start")
def nest_start(
    site_id: str = Query(...),
    device_name: str = Query("Google Nest"),
    db: Session = Depends(get_db),
):
    """Initiate the Google Nest OAuth consent flow (SDM API)."""
    client_id = settings.NEST_CLIENT_ID

    if _is_mock(client_id):
        mock_creds = {
            "access_token": f"mock-nest-{uuid.uuid4().hex[:12]}",
            "refresh_token": f"mock-nest-refresh-{uuid.uuid4().hex[:12]}",
            "token_type": "Bearer",
            "expires_in": 3600,
            "provider": "nest",
        }
        _create_device(
            db,
            site_id=site_id,
            device_name=device_name,
            device_type="thermostat",
            brand="nest",
            credentials=mock_creds,
        )
        redirect = f"{_frontend_url()}/dashboard/sites/{site_id}?oauth=success&provider=nest"
        return {"redirect_url": redirect, "mock": True}

    state = f"site_id:{site_id}|device_name:{device_name}"
    params = {
        "client_id": client_id,
        "redirect_uri": f"{_backend_base_url()}/api/v1/auth/nest/callback",
        "response_type": "code",
        "scope": NEST_SDM_SCOPE,
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    redirect_url = f"{NEST_AUTHORIZE_URL}?{urlencode(params)}"
    return {"redirect_url": redirect_url}


@router.get("/nest/callback")
async def nest_callback(
    code: str = Query(...),
    state: str = Query(""),
    db: Session = Depends(get_db),
):
    """Handle the Google Nest OAuth callback."""
    state_parts = dict(part.split(":", 1) for part in state.split("|") if ":" in part)
    site_id = state_parts.get("site_id", "")
    device_name = state_parts.get("device_name", "Google Nest")

    if not site_id:
        raise HTTPException(status_code=400, detail="Missing site_id in state")

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            NEST_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": settings.NEST_CLIENT_ID,
                "client_secret": settings.NEST_CLIENT_SECRET,
                "redirect_uri": f"{_backend_base_url()}/api/v1/auth/nest/callback",
            },
        )

    if resp.status_code != 200:
        logger.error("Nest token exchange failed: %s %s", resp.status_code, resp.text)
        return RedirectResponse(
            f"{_frontend_url()}/dashboard/sites/{site_id}?oauth=error&provider=nest"
        )

    tokens = resp.json()
    tokens["provider"] = "nest"

    _create_device(
        db,
        site_id=site_id,
        device_name=device_name,
        device_type="thermostat",
        brand="nest",
        credentials=tokens,
    )

    return RedirectResponse(
        f"{_frontend_url()}/dashboard/sites/{site_id}?oauth=success&provider=nest"
    )
