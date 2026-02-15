"""Billing endpoints: Stripe checkout, portal, and webhooks."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.config import settings
from app.models.subscription import Subscription
from app.models.user import Organization, User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/billing", tags=["billing"])

# ── Plan → Stripe Price ID mapping ──────────────────────────────────────

PLAN_PRICES: dict[str, str] = {
    "starter": settings.STRIPE_PRICE_STARTER,
    "pro": settings.STRIPE_PRICE_PRO,
    "enterprise": settings.STRIPE_PRICE_ENTERPRISE,
}

PLAN_AMOUNTS: dict[str, float] = {
    "free": 0.0,
    "starter": 100.0,
    "pro": 200.0,
    "enterprise": 500.0,
}


def _get_stripe():
    """Lazy-import stripe and configure the API key."""
    try:
        import stripe
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stripe SDK not installed.",
        )
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stripe is not configured. Set STRIPE_SECRET_KEY in environment.",
        )
    stripe.api_key = settings.STRIPE_SECRET_KEY
    return stripe


# ── Checkout session ─────────────────────────────────────────────────────


@router.post("/checkout")
def create_checkout_session(
    plan: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Create a Stripe Checkout session for the given plan.

    Returns ``{"checkout_url": "..."}`` that the frontend should redirect to.
    """
    stripe = _get_stripe()

    if plan not in PLAN_PRICES or not PLAN_PRICES[plan]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid or unconfigured plan: {plan}",
        )

    # Find or create Stripe customer
    org: Organization | None = (
        db.query(Organization)
        .filter(Organization.id == current_user.organization_id)
        .first()
    )
    sub: Subscription | None = (
        db.query(Subscription)
        .filter(Subscription.organization_id == current_user.organization_id)
        .first()
    )

    customer_id = sub.stripe_customer_id if sub else None

    if not customer_id:
        customer = stripe.Customer.create(
            email=current_user.email,
            name=org.name if org else current_user.full_name,
            metadata={"organization_id": current_user.organization_id or ""},
        )
        customer_id = customer.id
        if sub:
            sub.stripe_customer_id = customer_id
            db.commit()

    session = stripe.checkout.Session.create(
        customer=customer_id,
        mode="subscription",
        line_items=[{"price": PLAN_PRICES[plan], "quantity": 1}],
        success_url=f"{settings.FRONTEND_URL}/dashboard/settings?checkout=success",
        cancel_url=f"{settings.FRONTEND_URL}/dashboard/settings?checkout=cancel",
        metadata={
            "organization_id": current_user.organization_id or "",
            "plan": plan,
        },
    )

    return {"checkout_url": session.url}


# ── Customer portal ──────────────────────────────────────────────────────


@router.post("/portal")
def create_portal_session(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Create a Stripe Customer Portal session for managing the subscription."""
    stripe = _get_stripe()

    sub: Subscription | None = (
        db.query(Subscription)
        .filter(Subscription.organization_id == current_user.organization_id)
        .first()
    )

    if not sub or not sub.stripe_customer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active Stripe subscription found. Please subscribe first.",
        )

    session = stripe.billing_portal.Session.create(
        customer=sub.stripe_customer_id,
        return_url=f"{settings.FRONTEND_URL}/dashboard/settings",
    )

    return {"portal_url": session.url}


# ── Current subscription info ────────────────────────────────────────────


@router.get("/subscription")
def get_subscription(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Return the current subscription details for the user's organization."""
    sub: Subscription | None = (
        db.query(Subscription)
        .filter(Subscription.organization_id == current_user.organization_id)
        .first()
    )
    if not sub:
        return {"plan": "free", "status": "active", "monthly_price_eur": 0}

    return {
        "plan": sub.plan,
        "status": sub.status,
        "monthly_price_eur": sub.monthly_price_eur or PLAN_AMOUNTS.get(sub.plan, 0),
        "stripe_customer_id": sub.stripe_customer_id,
        "start_date": sub.start_date.isoformat() if sub.start_date else None,
        "end_date": sub.end_date.isoformat() if sub.end_date else None,
    }


# ── Stripe webhook ───────────────────────────────────────────────────────


@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Stripe webhook events (checkout.session.completed, etc.)."""
    stripe = _get_stripe()

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except (ValueError, stripe.error.SignatureVerificationError) as e:
        logger.warning("Stripe webhook signature verification failed: %s", e)
        raise HTTPException(status_code=400, detail="Invalid signature")

    event_type = event["type"]
    data = event["data"]["object"]

    if event_type == "checkout.session.completed":
        _handle_checkout_completed(db, data)
    elif event_type == "customer.subscription.updated":
        _handle_subscription_updated(db, data)
    elif event_type == "customer.subscription.deleted":
        _handle_subscription_deleted(db, data)
    else:
        logger.info("Unhandled Stripe event: %s", event_type)

    return {"status": "ok"}


def _handle_checkout_completed(db: Session, session: dict) -> None:
    """Process a successful checkout: update subscription records."""
    org_id = session.get("metadata", {}).get("organization_id")
    plan = session.get("metadata", {}).get("plan", "pro")
    customer_id = session.get("customer")
    stripe_sub_id = session.get("subscription")

    if not org_id:
        logger.warning("checkout.session.completed missing organization_id in metadata")
        return

    sub = db.query(Subscription).filter(Subscription.organization_id == org_id).first()
    if sub:
        sub.plan = plan
        sub.status = "active"
        sub.monthly_price_eur = PLAN_AMOUNTS.get(plan, 0)
        sub.stripe_customer_id = customer_id
        sub.stripe_subscription_id = stripe_sub_id
    else:
        sub = Subscription(
            organization_id=org_id,
            plan=plan,
            status="active",
            monthly_price_eur=PLAN_AMOUNTS.get(plan, 0),
            stripe_customer_id=customer_id,
            stripe_subscription_id=stripe_sub_id,
        )
        db.add(sub)

    # Also update Organization tier
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if org:
        org.subscription_tier = plan
        org.subscription_status = "active"

    db.commit()
    logger.info("Subscription updated for org %s: plan=%s", org_id, plan)


def _handle_subscription_updated(db: Session, stripe_sub: dict) -> None:
    """Handle subscription changes (upgrades, downgrades)."""
    customer_id = stripe_sub.get("customer")
    sub = (
        db.query(Subscription)
        .filter(Subscription.stripe_customer_id == customer_id)
        .first()
    )
    if not sub:
        return

    stripe_status = stripe_sub.get("status", "active")
    sub.status = "active" if stripe_status == "active" else stripe_status
    sub.stripe_subscription_id = stripe_sub.get("id")
    db.commit()


def _handle_subscription_deleted(db: Session, stripe_sub: dict) -> None:
    """Handle subscription cancellation."""
    customer_id = stripe_sub.get("customer")
    sub = (
        db.query(Subscription)
        .filter(Subscription.stripe_customer_id == customer_id)
        .first()
    )
    if not sub:
        return

    sub.status = "cancelled"
    org = db.query(Organization).filter(Organization.id == sub.organization_id).first()
    if org:
        org.subscription_status = "cancelled"

    db.commit()
    logger.info("Subscription cancelled for customer %s", customer_id)
