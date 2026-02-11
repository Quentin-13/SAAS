"""Tests for authentication endpoints (/api/v1/auth/*)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.models.user import User


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


class TestRegister:
    """POST /api/v1/auth/register"""

    def test_register_success(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "securepass123",
                "full_name": "New User",
                "organization_name": "New Org",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_register_duplicate_email(
        self, client: TestClient, test_user: User
    ) -> None:
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",  # same as test_user
                "password": "anotherpass123",
                "full_name": "Duplicate User",
                "organization_name": "Dup Org",
            },
        )
        assert response.status_code == 409


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------


class TestLogin:
    """POST /api/v1/auth/login (OAuth2 form)"""

    def test_login_success(self, client: TestClient, test_user: User) -> None:
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "test@example.com", "password": "testpassword123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client: TestClient, test_user: User) -> None:
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "test@example.com", "password": "wrongpassword"},
        )
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "nobody@example.com", "password": "nopassword"},
        )
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# Current user
# ---------------------------------------------------------------------------


class TestMe:
    """GET /api/v1/auth/me"""

    def test_get_me(
        self, client: TestClient, auth_headers: dict[str, str], test_user: User
    ) -> None:
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["full_name"] == "Test User"
        assert data["is_active"] is True

    def test_get_me_unauthorized(self, client: TestClient) -> None:
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# Token refresh
# ---------------------------------------------------------------------------


class TestRefreshToken:
    """POST /api/v1/auth/refresh"""

    def test_refresh_token(self, client: TestClient, test_user: User) -> None:
        # First, log in to get a refresh_token.
        login_resp = client.post(
            "/api/v1/auth/login",
            data={"username": "test@example.com", "password": "testpassword123"},
        )
        assert login_resp.status_code == 200
        refresh_token = login_resp.json()["refresh_token"]

        # Exchange the refresh token for a new pair.
        refresh_resp = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert refresh_resp.status_code == 200
        data = refresh_resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        # The new access token should be different from the original one.
        assert data["access_token"] != login_resp.json()["access_token"]
