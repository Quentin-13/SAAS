"""Site and Zone models."""

from __future__ import annotations

import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship

from app.database import Base


class Site(Base):
    __tablename__ = "sites"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    address = Column(String(500), nullable=True)
    postal_code = Column(String(20), nullable=True)
    city = Column(String(255), nullable=True)
    country = Column(String(10), nullable=False, default="FR")
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    surface_area = Column(Integer, nullable=True, comment="Surface area in m²")
    building_type = Column(
        String(30),
        nullable=True,
        comment="office | retail | warehouse | hotel | restaurant",
    )
    owner_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    organization_id = Column(
        String(36),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
    )
    autopilot_enabled = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # ── Relationships ───────────────────────────────────────────────────
    owner = relationship("User", back_populates="owned_sites")
    organization = relationship("Organization", back_populates="sites")
    zones = relationship("Zone", back_populates="site", lazy="selectin", cascade="all, delete-orphan")
    devices = relationship("Device", back_populates="site", lazy="selectin", cascade="all, delete-orphan")
    energy_forecasts = relationship("EnergyForecast", back_populates="site", lazy="selectin", cascade="all, delete-orphan")
    autopilot_actions = relationship("AutopilotAction", back_populates="site", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Site {self.name!r} ({self.city})>"


class Zone(Base):
    __tablename__ = "zones"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    site_id = Column(
        String(36),
        ForeignKey("sites.id", ondelete="CASCADE"),
        nullable=False,
    )
    name = Column(String(255), nullable=False)
    zone_type = Column(
        String(30),
        nullable=True,
        comment="office | meeting_room | warehouse | common_area",
    )
    surface_area = Column(Integer, nullable=True, comment="Surface area in m²")
    target_temp_min = Column(Float, default=19.0, nullable=False)
    target_temp_max = Column(Float, default=22.0, nullable=False)
    occupancy_schedule = Column(JSON, nullable=True)

    # ── Relationships ───────────────────────────────────────────────────
    site = relationship("Site", back_populates="zones")
    devices = relationship("Device", back_populates="zone", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Zone {self.name!r} ({self.zone_type})>"
