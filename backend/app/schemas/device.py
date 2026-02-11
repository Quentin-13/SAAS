from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict


class DeviceCreate(BaseModel):
    site_id: str
    zone_id: Optional[str] = None
    device_type: str
    brand: str
    model: Optional[str] = None
    external_id: Optional[str] = None
    name: str
    is_controllable: bool = False
    capabilities: Optional[Dict[str, Any]] = None


class DeviceUpdate(BaseModel):
    site_id: Optional[str] = None
    zone_id: Optional[str] = None
    device_type: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    external_id: Optional[str] = None
    name: Optional[str] = None
    is_controllable: Optional[bool] = None
    capabilities: Optional[Dict[str, Any]] = None


class DeviceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    site_id: str
    zone_id: Optional[str] = None
    device_type: str
    brand: str
    model: Optional[str] = None
    external_id: Optional[str] = None
    name: str
    is_controllable: bool
    capabilities: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class DeviceControlRequest(BaseModel):
    command: str  # e.g. "set_temperature", "set_mode"
    params: Dict[str, Any]
