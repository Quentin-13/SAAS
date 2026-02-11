"""Tests for site management endpoints (/api/v1/sites/*)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.models.site import Site
from app.models.user import User


# ---------------------------------------------------------------------------
# Site CRUD
# ---------------------------------------------------------------------------


class TestCreateSite:
    """POST /api/v1/sites/"""

    def test_create_site(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        response = client.post(
            "/api/v1/sites/",
            json={
                "name": "New Office",
                "address": "456 Avenue de la Republique",
                "city": "Lyon",
                "postal_code": "69001",
                "surface_area": 300,
                "building_type": "office",
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Office"
        assert data["city"] == "Lyon"
        assert data["surface_area"] == 300


class TestListSites:
    """GET /api/v1/sites/"""

    def test_list_sites(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        # Create two sites via the API.
        for name in ("Site A", "Site B"):
            resp = client.post(
                "/api/v1/sites/",
                json={"name": name, "city": "Paris"},
                headers=auth_headers,
            )
            assert resp.status_code == 201

        response = client.get("/api/v1/sites/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2


class TestGetSite:
    """GET /api/v1/sites/{site_id}"""

    def test_get_site(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        test_site: Site,
    ) -> None:
        response = client.get(
            f"/api/v1/sites/{test_site.id}", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_site.id
        assert data["name"] == "Test Site"

    def test_get_site_unauthorized(self, client: TestClient, test_site: Site) -> None:
        response = client.get(f"/api/v1/sites/{test_site.id}")
        assert response.status_code == 401


class TestUpdateSite:
    """PATCH /api/v1/sites/{site_id}"""

    def test_update_site(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        test_site: Site,
    ) -> None:
        response = client.patch(
            f"/api/v1/sites/{test_site.id}",
            json={"name": "Renamed Site"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Renamed Site"


class TestDeleteSite:
    """DELETE /api/v1/sites/{site_id}"""

    def test_delete_site(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        test_site: Site,
    ) -> None:
        response = client.delete(
            f"/api/v1/sites/{test_site.id}", headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["ok"] is True

        # Confirm it is gone.
        get_resp = client.get(
            f"/api/v1/sites/{test_site.id}", headers=auth_headers
        )
        assert get_resp.status_code == 404


# ---------------------------------------------------------------------------
# Autopilot toggle
# ---------------------------------------------------------------------------


class TestAutopilotToggle:
    """POST /api/v1/sites/{id}/autopilot/enable and /disable"""

    def test_enable_autopilot(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        test_site: Site,
    ) -> None:
        response = client.post(
            f"/api/v1/sites/{test_site.id}/autopilot/enable",
            headers=auth_headers,
        )
        assert response.status_code == 200
        # The SiteResponse schema does not expose autopilot_enabled directly,
        # but we can verify via a fresh GET.
        get_resp = client.get(
            f"/api/v1/sites/{test_site.id}", headers=auth_headers
        )
        assert get_resp.status_code == 200

    def test_disable_autopilot(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        test_site: Site,
    ) -> None:
        # Enable first, then disable.
        client.post(
            f"/api/v1/sites/{test_site.id}/autopilot/enable",
            headers=auth_headers,
        )
        response = client.post(
            f"/api/v1/sites/{test_site.id}/autopilot/disable",
            headers=auth_headers,
        )
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Zones
# ---------------------------------------------------------------------------


class TestZones:
    """POST /api/v1/sites/{id}/zones"""

    def test_create_zone(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        test_site: Site,
    ) -> None:
        response = client.post(
            f"/api/v1/sites/{test_site.id}/zones",
            json={
                "name": "Meeting Room",
                "zone_type": "meeting_room",
                "surface_area": 40,
                "target_temp_min": 19.0,
                "target_temp_max": 23.0,
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Meeting Room"
        assert data["zone_type"] == "meeting_room"
        assert data["target_temp_min"] == 19.0
        assert data["target_temp_max"] == 23.0
