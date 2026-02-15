"""Subscription model."""

from __future__ import annotations

import uuid

from sqlalchemy import Column, DateTime, Float, ForeignKey, String, func
from sqlalchemy.orm import relationship

from app.database import Base


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(
        String(36),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    plan = Column(
        String(20),
        nullable=False,
        default="free",
        comment="free | pro | enterprise",
    )
    status = Column(
        String(20),
        nullable=False,
        default="active",
        comment="active | cancelled | expired",
    )
    monthly_price_eur = Column(Float, nullable=True)
    stripe_customer_id = Column(String(255), nullable=True)
    stripe_subscription_id = Column(String(255), nullable=True)
    start_date = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    end_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # ── Relationships ───────────────────────────────────────────────────
    organization = relationship("Organization", back_populates="subscriptions")

    def __repr__(self) -> str:
        return f"<Subscription org={self.organization_id!r} plan={self.plan}>"
