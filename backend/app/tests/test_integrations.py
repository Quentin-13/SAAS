"""Tests for third-party integration clients and the energy forecaster (mock mode)."""

from __future__ import annotations

import asyncio

import pytest

from app.services.integrations.weather import WeatherClient
from app.services.integrations.nest import NestClient
from app.services.integrations.netatmo import NetatmoClient
from app.services.integrations.linky import LinkyClient
from app.services.ml.forecasting import generate_mock_forecast


def _run(coro):
    """Convenience helper to run a coroutine synchronously."""
    return asyncio.get_event_loop().run_until_complete(coro)


# ---------------------------------------------------------------------------
# WeatherClient (mock)
# ---------------------------------------------------------------------------


class TestWeatherClient:
    """Tests for WeatherClient in mock mode."""

    @pytest.fixture()
    def weather(self) -> WeatherClient:
        return WeatherClient(api_key="fake-key", mock_mode=True)

    def test_weather_mock_current(self, weather: WeatherClient) -> None:
        data = _run(weather.get_current(lat=48.8566, lon=2.3522))
        assert "temp_celsius" in data
        assert "humidity" in data
        assert "description" in data
        assert "wind_speed" in data
        assert isinstance(data["temp_celsius"], float)

    def test_weather_mock_forecast(self, weather: WeatherClient) -> None:
        forecasts = _run(weather.get_forecast_48h(lat=48.8566, lon=2.3522))
        assert isinstance(forecasts, list)
        assert len(forecasts) == 16  # 16 x 3h = 48h
        first = forecasts[0]
        assert "temp_celsius" in first
        assert "time" in first
        assert "humidity" in first


# ---------------------------------------------------------------------------
# NestClient (mock)
# ---------------------------------------------------------------------------


class TestNestClient:
    """Tests for NestClient in mock mode."""

    @pytest.fixture()
    def nest(self) -> NestClient:
        return NestClient(mock_mode=True)

    def test_nest_mock_discover(self, nest: NestClient) -> None:
        devices = _run(
            nest.discover_devices(
                access_token="fake-token",
                project_id="mock-project",
            )
        )
        assert isinstance(devices, list)
        assert len(devices) >= 1
        first = devices[0]
        assert "device_id" in first
        assert "room" in first
        assert "type" in first

    def test_nest_mock_set_temperature(self, nest: NestClient) -> None:
        result = _run(
            nest.set_temperature(
                access_token="fake-token",
                project_id="mock-project",
                device_id="nest-thermo-001",
                temp=21.5,
            )
        )
        assert result is True


# ---------------------------------------------------------------------------
# NetatmoClient (mock)
# ---------------------------------------------------------------------------


class TestNetatmoClient:
    """Tests for NetatmoClient in mock mode."""

    @pytest.fixture()
    def netatmo(self) -> NetatmoClient:
        return NetatmoClient(mock_mode=True)

    def test_netatmo_mock_thermostats(self, netatmo: NetatmoClient) -> None:
        modules = _run(netatmo.get_thermostats(access_token="fake-token"))
        assert isinstance(modules, list)
        assert len(modules) >= 1
        first = modules[0]
        assert "id" in first
        assert "name" in first
        assert "measured_temperature" in first


# ---------------------------------------------------------------------------
# LinkyClient (mock)
# ---------------------------------------------------------------------------


class TestLinkyClient:
    """Tests for LinkyClient in mock mode."""

    @pytest.fixture()
    def linky(self) -> LinkyClient:
        return LinkyClient(mock_mode=True)

    def test_linky_mock_consumption(self, linky: LinkyClient) -> None:
        data = _run(
            linky.get_consumption(
                access_token="fake-token",
                usage_point_id="12345678901234",
                start="2025-01-01",
                end="2025-01-03",
            )
        )
        assert isinstance(data, list)
        assert len(data) > 0
        first = data[0]
        assert "time" in first
        assert "power_kw" in first
        assert "energy_kwh" in first
        assert isinstance(first["power_kw"], float)


# ---------------------------------------------------------------------------
# EnergyForecaster mock helper
# ---------------------------------------------------------------------------


class TestEnergyForecasterMock:
    """Tests for the generate_mock_forecast module-level helper."""

    def test_forecaster_mock(self) -> None:
        forecasts = generate_mock_forecast(site_id="site-demo", days=2)
        assert isinstance(forecasts, list)
        assert len(forecasts) == 48  # 2 days * 24 hours
        first = forecasts[0]
        assert "forecast_date" in first
        assert "predicted_kwh" in first
        assert "predicted_cost_eur" in first
        assert "confidence_lower" in first
        assert "confidence_upper" in first
        assert "horizon_hours" in first
        assert first["predicted_kwh"] > 0
        assert first["predicted_cost_eur"] > 0
        assert first["confidence_lower"] <= first["predicted_kwh"]
        assert first["confidence_upper"] >= first["predicted_kwh"]
