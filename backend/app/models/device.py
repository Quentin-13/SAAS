"""Device model."""

from __future__ import annotations

import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship

from app.database import Base


class Device(Base):
    __tablename__ = "devices"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    site_id = Column(
        String(36),
        ForeignKey("sites.id", ondelete="CASCADE"),
        nullable=False,
    )
    zone_id = Column(
        String(36),
        ForeignKey("zones.id", ondelete="SET NULL"),
        nullable=True,
    )
    device_type = Column(
        String(30),
        nullable=False,
        comment="thermostat | meter | water_heater | hvac | lighting",
    )
    brand = Column(
        String(30),
        nullable=True,
        comment="nest | netatmo | tado | linky | generic",
    )
    model = Column(String(255), nullable=True)
    external_id = Column(String(255), unique=True, nullable=True)
    name = Column(String(255), nullable=True)
    is_controllable = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    capabilities = Column(JSON, nullable=True)
    current_state = Column(JSON, nullable=True)
    api_credentials = Column(JSON, nullable=True)
    last_sync = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # ── Relationships ───────────────────────────────────────────────────
    site = relationship("Site", back_populates="devices")
    zone = relationship("Zone", back_populates="devices")
    energy_readings = relationship("EnergyReading", back_populates="device", lazy="selectin")
    autopilot_actions = relationship("AutopilotAction", back_populates="device", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Device {self.name!r} ({self.device_type}/{self.brand})>"
