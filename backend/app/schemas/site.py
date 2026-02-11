from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class BuildingType(str, Enum):
    office = "office"
    retail = "retail"
    warehouse = "warehouse"
    hotel = "hotel"
    restaurant = "restaurant"


class SiteCreate(BaseModel):
    name: str
    address: Optional[str] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    surface_area: Optional[int] = None
    building_type: Optional[BuildingType] = None


class SiteUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    surface_area: Optional[int] = None
    building_type: Optional[BuildingType] = None


class SiteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    name: str
    address: Optional[str] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    surface_area: Optional[int] = None
    building_type: Optional[str] = None
    zones_count: Optional[int] = None
    devices_count: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class ZoneCreate(BaseModel):
    name: str
    zone_type: Optional[str] = None
    surface_area: Optional[int] = None
    target_temp_min: float = 19.0
    target_temp_max: float = 22.0
    occupancy_schedule: Optional[Dict[str, Any]] = None


class ZoneResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    site_id: str
    name: str
    zone_type: Optional[str] = None
    surface_area: Optional[int] = None
    target_temp_min: float
    target_temp_max: float
    occupancy_schedule: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
