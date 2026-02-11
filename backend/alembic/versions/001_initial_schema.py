"""Initial schema with all tables and TimescaleDB hypertable.

Revision ID: 001
Revises: None
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable TimescaleDB extension
    op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;")

    # Organizations
    op.create_table(
        "organizations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("subscription_tier", sa.String(20), server_default="free"),
        sa.Column("subscription_status", sa.String(20), server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Users
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("email", sa.String(), nullable=False, unique=True, index=True),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.Column("full_name", sa.String()),
        sa.Column("phone", sa.String()),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("is_superuser", sa.Boolean(), server_default="false"),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )

    # Sites
    op.create_table(
        "sites",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("address", sa.String()),
        sa.Column("postal_code", sa.String()),
        sa.Column("city", sa.String()),
        sa.Column("country", sa.String(), server_default="FR"),
        sa.Column("latitude", sa.Float()),
        sa.Column("longitude", sa.Float()),
        sa.Column("surface_area", sa.Integer()),
        sa.Column("building_type", sa.String(20)),
        sa.Column("owner_id", sa.String(36), sa.ForeignKey("users.id")),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id")),
        sa.Column("autopilot_enabled", sa.Boolean(), server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_sites_owner_id", "sites", ["owner_id"])
    op.create_index("ix_sites_organization_id", "sites", ["organization_id"])

    # Zones
    op.create_table(
        "zones",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("site_id", sa.String(36), sa.ForeignKey("sites.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("zone_type", sa.String(20)),
        sa.Column("surface_area", sa.Integer()),
        sa.Column("target_temp_min", sa.Float(), server_default="19.0"),
        sa.Column("target_temp_max", sa.Float(), server_default="22.0"),
        sa.Column("occupancy_schedule", sa.JSON()),
    )
    op.create_index("ix_zones_site_id", "zones", ["site_id"])

    # Devices
    op.create_table(
        "devices",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("site_id", sa.String(36), sa.ForeignKey("sites.id", ondelete="CASCADE"), nullable=False),
        sa.Column("zone_id", sa.String(36), sa.ForeignKey("zones.id"), nullable=True),
        sa.Column("device_type", sa.String(20)),
        sa.Column("brand", sa.String(20)),
        sa.Column("model", sa.String()),
        sa.Column("external_id", sa.String(), unique=True),
        sa.Column("name", sa.String()),
        sa.Column("is_controllable", sa.Boolean(), server_default="false"),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("capabilities", sa.JSON()),
        sa.Column("current_state", sa.JSON()),
        sa.Column("api_credentials", sa.JSON()),
        sa.Column("last_sync", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_devices_site_id", "devices", ["site_id"])
    op.create_index("ix_devices_zone_id", "devices", ["zone_id"])

    # Energy Readings (TimescaleDB hypertable)
    op.create_table(
        "energy_readings",
        sa.Column("time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("device_id", sa.String(36), sa.ForeignKey("devices.id"), nullable=False),
        sa.Column("power_kw", sa.Float()),
        sa.Column("energy_kwh", sa.Float()),
        sa.Column("cost_eur", sa.Float()),
        sa.Column("temperature", sa.Float()),
        sa.Column("humidity", sa.Float()),
        sa.Column("tariff_type", sa.String(20)),
        sa.Column("outdoor_temp", sa.Float()),
        sa.Column("is_occupied", sa.Boolean()),
        sa.PrimaryKeyConstraint("time", "device_id"),
    )
    op.create_index("ix_energy_readings_device_id", "energy_readings", ["device_id"])
    op.create_index("ix_energy_readings_time", "energy_readings", ["time"])

    # Convert to TimescaleDB hypertable
    op.execute("SELECT create_hypertable('energy_readings', 'time', if_not_exists => TRUE);")

    # Energy Forecasts
    op.create_table(
        "energy_forecasts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("site_id", sa.String(36), sa.ForeignKey("sites.id"), nullable=False),
        sa.Column("forecast_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("horizon_hours", sa.Integer()),
        sa.Column("predicted_kwh", sa.Float()),
        sa.Column("predicted_cost_eur", sa.Float()),
        sa.Column("confidence_lower", sa.Float()),
        sa.Column("confidence_upper", sa.Float()),
        sa.Column("model_version", sa.String()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_energy_forecasts_site_id", "energy_forecasts", ["site_id"])

    # Autopilot Actions
    op.create_table(
        "autopilot_actions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("site_id", sa.String(36), sa.ForeignKey("sites.id"), nullable=False),
        sa.Column("device_id", sa.String(36), sa.ForeignKey("devices.id"), nullable=False),
        sa.Column("action_type", sa.String(30), nullable=False),
        sa.Column("action_params", sa.JSON()),
        sa.Column("reasoning", sa.Text()),
        sa.Column("predicted_savings_eur", sa.Float()),
        sa.Column("predicted_savings_kwh", sa.Float()),
        sa.Column("confidence_score", sa.Float()),
        sa.Column("status", sa.String(20), server_default="pending"),
        sa.Column("executed_at", sa.DateTime(timezone=True)),
        sa.Column("result", sa.JSON()),
        sa.Column("error_message", sa.Text()),
        sa.Column("actual_savings_eur", sa.Float()),
        sa.Column("actual_savings_kwh", sa.Float()),
        sa.Column("comfort_impact", sa.String(20)),
        sa.Column("user_feedback", sa.String(20)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_autopilot_actions_site_id", "autopilot_actions", ["site_id"])
    op.create_index("ix_autopilot_actions_device_id", "autopilot_actions", ["device_id"])
    op.create_index("ix_autopilot_actions_status", "autopilot_actions", ["status"])

    # Subscriptions
    op.create_table(
        "subscriptions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("plan", sa.String(20), server_default="free"),
        sa.Column("status", sa.String(20), server_default="active"),
        sa.Column("monthly_price_eur", sa.Float()),
        sa.Column("start_date", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("end_date", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("subscriptions")
    op.drop_table("autopilot_actions")
    op.drop_table("energy_forecasts")
    op.drop_table("energy_readings")
    op.drop_table("devices")
    op.drop_table("zones")
    op.drop_table("sites")
    op.drop_table("users")
    op.drop_table("organizations")
