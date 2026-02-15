"""Pydantic schemas for admin API endpoints."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


# ── User admin schemas ──────────────────────────────────────────────────

class AdminUserUpdate(BaseModel):
    is_active: Optional[bool] = None
    role: Optional[str] = None
    reset_password: Optional[str] = None


class AdminUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    full_name: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool
    is_superuser: bool
    role: str
    organization_id: Optional[str] = None
    organization_name: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


# ── Organization admin schemas ──────────────────────────────────────────

class AdminOrgResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    subscription_tier: str
    subscription_status: str
    created_at: datetime
    user_count: int = 0
    site_count: int = 0


class AdminOrgCreate(BaseModel):
    name: str
    subscription_tier: str = "free"


# ── Subscription admin schemas ──────────────────────────────────────────

class AdminSubscriptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    organization_name: Optional[str] = None
    plan: str
    status: str
    monthly_price_eur: Optional[float] = None
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    start_date: datetime
    end_date: Optional[datetime] = None
    created_at: datetime


class AdminSubscriptionUpdate(BaseModel):
    plan: Optional[str] = None
    status: Optional[str] = None
    monthly_price_eur: Optional[float] = None


# ── Stats schemas ───────────────────────────────────────────────────────

class PlatformStats(BaseModel):
    total_users: int
    active_users: int
    total_organizations: int
    total_sites: int
    total_devices: int
    autopilot_actions_this_month: int
    total_revenue_monthly: float
    total_revenue_annual: float
    plans_distribution: dict[str, int]
    churn_rate: float
    new_users_this_month: int


# ── Activity log schemas ────────────────────────────────────────────────

class ActivityLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    action: str
    target_type: Optional[str] = None
    target_id: Optional[str] = None
    details: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime


# ── Pagination wrapper ──────────────────────────────────────────────────

class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    per_page: int
    pages: int
