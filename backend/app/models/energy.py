"""Energy reading and forecast models."""

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
from sqlalchemy.orm import relationship

from app.database import Base


class EnergyReading(Base):
    """Time-series energy readings.

    Uses a composite primary key of (time, device_id) which is
    well-suited for TimescaleDB hypertables.
    """

    __tablename__ = "energy_readings"

    time = Column(DateTime(timezone=True), primary_key=True, nullable=False)
    device_id = Column(
        String(36),
        ForeignKey("devices.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    power_kw = Column(Float, nullable=True)
    energy_kwh = Column(Float, nullable=True)
    cost_eur = Column(Float, nullable=True)
    temperature = Column(Float, nullable=True)
    humidity = Column(Float, nullable=True)
    tariff_type = Column(
        String(20),
        nullable=True,
        comment="peak | off_peak | super_off_peak",
    )
    outdoor_temp = Column(Float, nullable=True)
    is_occupied = Column(Boolean, nullable=True)

    # ── Relationships ───────────────────────────────────────────────────
    device = relationship("Device", back_populates="energy_readings")

    def __repr__(self) -> str:
        return f"<EnergyReading device={self.device_id!r} time={self.time}>"


class EnergyForecast(Base):
    __tablename__ = "energy_forecasts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    site_id = Column(
        String(36),
        ForeignKey("sites.id", ondelete="CASCADE"),
        nullable=False,
    )
    forecast_date = Column(DateTime(timezone=True), nullable=False)
    horizon_hours = Column(Integer, nullable=False)
    predicted_kwh = Column(Float, nullable=True)
    predicted_cost_eur = Column(Float, nullable=True)
    confidence_lower = Column(Float, nullable=True)
    confidence_upper = Column(Float, nullable=True)
    model_version = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # ── Relationships ───────────────────────────────────────────────────
    site = relationship("Site", back_populates="energy_forecasts")

    def __repr__(self) -> str:
        return f"<EnergyForecast site={self.site_id!r} date={self.forecast_date}>"
