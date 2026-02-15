"""Admin API endpoints — protected by admin role check."""

from __future__ import annotations

import csv
import io
import math
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin_user, get_db
from app.models.action import AutopilotAction
from app.models.activity_log import ActivityLog
from app.models.device import Device
from app.models.site import Site
from app.models.subscription import Subscription
from app.models.user import Organization, User
from app.schemas.admin import (
    ActivityLogResponse,
    AdminOrgCreate,
    AdminOrgResponse,
    AdminSubscriptionResponse,
    AdminSubscriptionUpdate,
    AdminUserResponse,
    AdminUserUpdate,
    PlatformStats,
)
from app.utils.security import get_password_hash

router = APIRouter(prefix="/admin", tags=["admin"])


# ── Helpers ──────────────────────────────────────────────────────────────

def _log_action(
    db: Session,
    user: User,
    action: str,
    target_type: str | None = None,
    target_id: str | None = None,
    details: str | None = None,
    ip: str | None = None,
) -> None:
    log = ActivityLog(
        user_id=user.id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details,
        ip_address=ip,
    )
    db.add(log)
    db.flush()


def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


# ── Ping ─────────────────────────────────────────────────────────────────

@router.get("/ping")
def admin_ping(admin: User = Depends(get_current_admin_user)):
    return {"status": "ok", "admin": admin.email, "role": admin.role}


# ── Users ────────────────────────────────────────────────────────────────

@router.get("/users")
def list_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: str = Query("", description="Filter by email or name"),
    role: str = Query("", description="Filter by role"),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    query = db.query(User)

    if search:
        pattern = f"%{search}%"
        query = query.filter(
            (User.email.ilike(pattern)) | (User.full_name.ilike(pattern))
        )
    if role:
        query = query.filter(User.role == role)

    total = query.count()
    users = (
        query.order_by(User.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    items = []
    for u in users:
        org_name = u.organization.name if u.organization else None
        items.append(
            AdminUserResponse(
                id=u.id,
                email=u.email,
                full_name=u.full_name,
                phone=u.phone,
                is_active=u.is_active,
                is_superuser=u.is_superuser,
                role=getattr(u, "role", "user"),
                organization_id=u.organization_id,
                organization_name=org_name,
                created_at=u.created_at,
                updated_at=u.updated_at,
            ).model_dump()
        )

    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": math.ceil(total / per_page) if total else 1,
    }


@router.patch("/users/{user_id}")
def update_user(
    user_id: str,
    body: AdminUserUpdate,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    changes = []
    if body.is_active is not None:
        user.is_active = body.is_active
        changes.append(f"is_active={body.is_active}")
    if body.role is not None:
        if body.role not in ("user", "admin"):
            raise HTTPException(status_code=400, detail="Role must be 'user' or 'admin'")
        user.role = body.role
        user.is_superuser = body.role == "admin"
        changes.append(f"role={body.role}")
    if body.reset_password:
        user.hashed_password = get_password_hash(body.reset_password)
        changes.append("password_reset")

    _log_action(db, admin, "user.update", "user", user_id, ", ".join(changes), _get_client_ip(request))
    db.commit()
    db.refresh(user)

    return AdminUserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        role=getattr(user, "role", "user"),
        organization_id=user.organization_id,
        organization_name=user.organization.name if user.organization else None,
        created_at=user.created_at,
        updated_at=user.updated_at,
    ).model_dump()


# ── Organizations ────────────────────────────────────────────────────────

@router.get("/organizations")
def list_organizations(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: str = Query(""),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    query = db.query(Organization)
    if search:
        query = query.filter(Organization.name.ilike(f"%{search}%"))

    total = query.count()
    orgs = (
        query.order_by(Organization.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    items = []
    for org in orgs:
        items.append(
            AdminOrgResponse(
                id=org.id,
                name=org.name,
                subscription_tier=org.subscription_tier,
                subscription_status=org.subscription_status,
                created_at=org.created_at,
                user_count=len(org.users) if org.users else 0,
                site_count=len(org.sites) if org.sites else 0,
            ).model_dump()
        )

    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": math.ceil(total / per_page) if total else 1,
    }


@router.post("/organizations", status_code=201)
def create_organization(
    body: AdminOrgCreate,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    org = Organization(name=body.name, subscription_tier=body.subscription_tier)
    db.add(org)
    _log_action(db, admin, "organization.create", "organization", None, body.name, _get_client_ip(request))
    db.commit()
    db.refresh(org)
    return AdminOrgResponse(
        id=org.id,
        name=org.name,
        subscription_tier=org.subscription_tier,
        subscription_status=org.subscription_status,
        created_at=org.created_at,
        user_count=0,
        site_count=0,
    ).model_dump()


@router.delete("/organizations/{org_id}")
def delete_organization(
    org_id: str,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    _log_action(db, admin, "organization.delete", "organization", org_id, org.name, _get_client_ip(request))
    db.delete(org)
    db.commit()
    return {"status": "deleted"}


# ── Subscriptions ────────────────────────────────────────────────────────

@router.get("/subscriptions")
def list_subscriptions(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status_filter: str = Query("", alias="status"),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    query = db.query(Subscription)
    if status_filter:
        query = query.filter(Subscription.status == status_filter)

    total = query.count()
    subs = (
        query.order_by(Subscription.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    items = []
    for s in subs:
        org_name = s.organization.name if s.organization else None
        items.append(
            AdminSubscriptionResponse(
                id=s.id,
                organization_id=s.organization_id,
                organization_name=org_name,
                plan=s.plan,
                status=s.status,
                monthly_price_eur=s.monthly_price_eur,
                stripe_customer_id=getattr(s, "stripe_customer_id", None),
                stripe_subscription_id=getattr(s, "stripe_subscription_id", None),
                start_date=s.start_date,
                end_date=s.end_date,
                created_at=s.created_at,
            ).model_dump()
        )

    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": math.ceil(total / per_page) if total else 1,
    }


@router.patch("/subscriptions/{sub_id}")
def update_subscription(
    sub_id: str,
    body: AdminSubscriptionUpdate,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    sub = db.query(Subscription).filter(Subscription.id == sub_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")

    changes = []
    if body.plan is not None:
        sub.plan = body.plan
        # Also update the org subscription_tier
        if sub.organization:
            sub.organization.subscription_tier = body.plan
        price_map = {"free": 0.0, "starter": 100.0, "pro": 200.0, "enterprise": 500.0}
        sub.monthly_price_eur = price_map.get(body.plan, sub.monthly_price_eur)
        changes.append(f"plan={body.plan}")
    if body.status is not None:
        sub.status = body.status
        if sub.organization:
            sub.organization.subscription_status = body.status
        if body.status == "cancelled":
            sub.end_date = datetime.now(timezone.utc) + timedelta(days=30)
        changes.append(f"status={body.status}")
    if body.monthly_price_eur is not None:
        sub.monthly_price_eur = body.monthly_price_eur
        changes.append(f"price={body.monthly_price_eur}")

    _log_action(db, admin, "subscription.update", "subscription", sub_id, ", ".join(changes), _get_client_ip(request))
    db.commit()
    db.refresh(sub)

    return AdminSubscriptionResponse(
        id=sub.id,
        organization_id=sub.organization_id,
        organization_name=sub.organization.name if sub.organization else None,
        plan=sub.plan,
        status=sub.status,
        monthly_price_eur=sub.monthly_price_eur,
        stripe_customer_id=getattr(sub, "stripe_customer_id", None),
        stripe_subscription_id=getattr(sub, "stripe_subscription_id", None),
        start_date=sub.start_date,
        end_date=sub.end_date,
        created_at=sub.created_at,
    ).model_dump()


# ── Stats ────────────────────────────────────────────────────────────────

@router.get("/stats", response_model=PlatformStats)
def get_platform_stats(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    total_users = db.query(func.count(User.id)).scalar() or 0
    active_users = db.query(func.count(User.id)).filter(User.is_active == True).scalar() or 0  # noqa: E712
    total_orgs = db.query(func.count(Organization.id)).scalar() or 0
    total_sites = db.query(func.count(Site.id)).scalar() or 0
    total_devices = db.query(func.count(Device.id)).scalar() or 0

    actions_this_month = (
        db.query(func.count(AutopilotAction.id))
        .filter(AutopilotAction.created_at >= month_start)
        .scalar() or 0
    )

    new_users_this_month = (
        db.query(func.count(User.id))
        .filter(User.created_at >= month_start)
        .scalar() or 0
    )

    # Revenue from active subscriptions
    monthly_revenue = (
        db.query(func.coalesce(func.sum(Subscription.monthly_price_eur), 0.0))
        .filter(Subscription.status == "active")
        .scalar() or 0.0
    )

    # Plans distribution
    plans = db.query(Subscription.plan, func.count(Subscription.id)).group_by(Subscription.plan).all()
    plans_dist = {p: c for p, c in plans}

    # Churn rate (cancelled in last 30 days / total active)
    cancelled_recently = (
        db.query(func.count(Subscription.id))
        .filter(
            Subscription.status == "cancelled",
            Subscription.end_date >= now - timedelta(days=30),
        )
        .scalar() or 0
    )
    active_subs = (
        db.query(func.count(Subscription.id))
        .filter(Subscription.status == "active")
        .scalar() or 1
    )
    churn = round((cancelled_recently / active_subs) * 100, 1)

    return PlatformStats(
        total_users=total_users,
        active_users=active_users,
        total_organizations=total_orgs,
        total_sites=total_sites,
        total_devices=total_devices,
        autopilot_actions_this_month=actions_this_month,
        total_revenue_monthly=float(monthly_revenue),
        total_revenue_annual=float(monthly_revenue) * 12,
        plans_distribution=plans_dist,
        churn_rate=churn,
        new_users_this_month=new_users_this_month,
    )


# ── Activity Logs ────────────────────────────────────────────────────────

@router.get("/logs")
def list_logs(
    page: int = Query(1, ge=1),
    per_page: int = Query(30, ge=1, le=100),
    action_filter: str = Query("", alias="action"),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    query = db.query(ActivityLog)
    if action_filter:
        query = query.filter(ActivityLog.action.ilike(f"%{action_filter}%"))

    total = query.count()
    logs = (
        query.order_by(ActivityLog.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    items = []
    for log in logs:
        items.append(
            ActivityLogResponse(
                id=log.id,
                user_id=log.user_id,
                user_email=log.user.email if log.user else None,
                action=log.action,
                target_type=log.target_type,
                target_id=log.target_id,
                details=log.details,
                ip_address=log.ip_address,
                created_at=log.created_at,
            ).model_dump()
        )

    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": math.ceil(total / per_page) if total else 1,
    }


# ── Export ───────────────────────────────────────────────────────────────

@router.get("/export/users")
def export_users_csv(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    users = db.query(User).order_by(User.created_at.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "email", "full_name", "role", "is_active", "organization_id", "created_at"])
    for u in users:
        writer.writerow([u.id, u.email, u.full_name, getattr(u, "role", "user"), u.is_active, u.organization_id, u.created_at])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=users_export.csv"},
    )
