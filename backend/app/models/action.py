"""Autopilot action model."""

from __future__ import annotations

import uuid

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship

from app.database import Base


class AutopilotAction(Base):
    __tablename__ = "autopilot_actions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    site_id = Column(
        String(36),
        ForeignKey("sites.id", ondelete="CASCADE"),
        nullable=False,
    )
    device_id = Column(
        String(36),
        ForeignKey("devices.id", ondelete="CASCADE"),
        nullable=False,
    )
    action_type = Column(
        String(30),
        nullable=False,
        comment="temperature_adjustment | mode_change | schedule_override | equipment_shutdown | load_shedding",
    )
    action_params = Column(JSON, nullable=True)
    reasoning = Column(Text, nullable=True)
    predicted_savings_eur = Column(Float, nullable=True)
    predicted_savings_kwh = Column(Float, nullable=True)
    confidence_score = Column(Float, nullable=True)
    status = Column(
        String(20),
        nullable=False,
        default="pending",
        comment="pending | executed | failed | rolled_back",
    )
    executed_at = Column(DateTime(timezone=True), nullable=True)
    result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    actual_savings_eur = Column(Float, nullable=True)
    actual_savings_kwh = Column(Float, nullable=True)
    comfort_impact = Column(
        String(20),
        nullable=True,
        comment="none | minimal | moderate | significant",
    )
    user_feedback = Column(
        String(20),
        nullable=True,
        comment="positive | neutral | negative",
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # ── Relationships ───────────────────────────────────────────────────
    site = relationship("Site", back_populates="autopilot_actions")
    device = relationship("Device", back_populates="autopilot_actions")

    def __repr__(self) -> str:
        return f"<AutopilotAction {self.action_type!r} status={self.status}>"
