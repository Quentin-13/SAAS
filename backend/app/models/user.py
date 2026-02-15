"""User and Organization models."""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, func
from sqlalchemy.orm import relationship

from app.database import Base


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    subscription_tier = Column(
        String(20),
        nullable=False,
        default="free",
        comment="free | pro | enterprise",
    )
    subscription_status = Column(
        String(20),
        nullable=False,
        default="active",
        comment="active | cancelled | expired",
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # ── Relationships ───────────────────────────────────────────────────
    users = relationship("User", back_populates="organization", lazy="selectin")
    sites = relationship("Site", back_populates="organization", lazy="selectin")
    subscriptions = relationship("Subscription", back_populates="organization", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Organization {self.name!r} ({self.subscription_tier})>"


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    role = Column(String(20), nullable=False, default="user", server_default="user",
                  comment="user | admin")
    organization_id = Column(
        String(36),
        ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # ── Relationships ───────────────────────────────────────────────────
    organization = relationship("Organization", back_populates="users")
    owned_sites = relationship("Site", back_populates="owner", lazy="selectin")

    def __repr__(self) -> str:
        return f"<User {self.email!r}>"
