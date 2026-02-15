"""Activity log model for tracking admin and user actions."""

from __future__ import annotations

import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import relationship

from app.database import Base


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(100), nullable=False, comment="e.g. user.create, subscription.cancel")
    target_type = Column(String(50), nullable=True, comment="e.g. user, organization, subscription")
    target_id = Column(String(36), nullable=True)
    details = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", lazy="selectin")

    def __repr__(self) -> str:
        return f"<ActivityLog {self.action!r} by={self.user_id}>"
