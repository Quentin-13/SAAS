"""Shared pytest fixtures for the Energy Management SaaS test suite."""

from __future__ import annotations

import uuid
from collections.abc import Generator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models.user import Organization, User
from app.models.site import Site, Zone
from app.models.device import Device
from app.utils.security import get_password_hash


# ---------------------------------------------------------------------------
# In-memory SQLite engine shared across all tests in a session
# ---------------------------------------------------------------------------
SQLALCHEMY_TEST_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_TEST_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# SQLite does not enforce foreign keys by default; enable them.
@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestingSessionLocal = sessionmaker(
    bind=engine, autocommit=False, autoflush=False,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """Create all tables, yield a session, then rollback and tear down."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """Provide a FastAPI ``TestClient`` that uses the test DB session."""

    def _override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as tc:
        yield tc
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user(db_session: Session) -> User:
    """Insert a user with known credentials and return the ORM object."""
    org = Organization(
        id=str(uuid.uuid4()),
        name="Test Organization",
    )
    db_session.add(org)
    db_session.flush()

    user = User(
        id=str(uuid.uuid4()),
        email="test@example.com",
        hashed_password=get_password_hash("testpassword123"),
        full_name="Test User",
        is_active=True,
        organization_id=org.id,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def auth_headers(client: TestClient, test_user: User) -> dict[str, str]:
    """Log in with ``test_user`` and return Bearer-token headers."""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "test@example.com", "password": "testpassword123"},
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def test_site(db_session: Session, test_user: User) -> Site:
    """Create a site belonging to ``test_user``."""
    site = Site(
        id=str(uuid.uuid4()),
        name="Test Site",
        address="123 Rue de Test",
        city="Paris",
        postal_code="75001",
        country="FR",
        surface_area=500,
        building_type="office",
        owner_id=test_user.id,
        organization_id=test_user.organization_id,
    )
    db_session.add(site)
    db_session.commit()
    db_session.refresh(site)
    return site


@pytest.fixture(scope="function")
def test_device(db_session: Session, test_site: Site) -> Device:
    """Create a thermostat device belonging to ``test_site``."""
    device = Device(
        id=str(uuid.uuid4()),
        site_id=test_site.id,
        device_type="thermostat",
        brand="nest",
        name="Office Thermostat",
        is_controllable=True,
        is_active=True,
    )
    db_session.add(device)
    db_session.commit()
    db_session.refresh(device)
    return device
