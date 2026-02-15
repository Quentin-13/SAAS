"""Add role column to users, stripe fields to subscriptions, activity_logs table.

Revision ID: 002
Revises: 001
Create Date: 2026-02-12 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add role column to users
    op.add_column("users", sa.Column("role", sa.String(20), server_default="user", nullable=False))

    # Add stripe fields to subscriptions
    op.add_column("subscriptions", sa.Column("stripe_customer_id", sa.String(255), nullable=True))
    op.add_column("subscriptions", sa.Column("stripe_subscription_id", sa.String(255), nullable=True))

    # Activity logs table
    op.create_table(
        "activity_logs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("target_type", sa.String(50), nullable=True),
        sa.Column("target_id", sa.String(36), nullable=True),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_activity_logs_user_id", "activity_logs", ["user_id"])
    op.create_index("ix_activity_logs_created_at", "activity_logs", ["created_at"])

    # Set admin role for superusers
    op.execute("UPDATE users SET role = 'admin' WHERE is_superuser = true")


def downgrade() -> None:
    op.drop_table("activity_logs")
    op.drop_column("subscriptions", "stripe_subscription_id")
    op.drop_column("subscriptions", "stripe_customer_id")
    op.drop_column("users", "role")
