"""OpenWeatherMap API integration."""
import logging
import random
from datetime import datetime, timedelta
from typing import Optional

from app.services.integrations.base import BaseIntegration

logger = logging.getLogger(__name__)


class WeatherClient(BaseIntegration):
    """Client for OpenWeatherMap API."""

    BASE_URL = "https://api.openweathermap.org"

    def __init__(self, api_key: Optional[str] = None, mock_mode: Optional[bool] = None):
        super().__init__(mock_mode=mock_mode)
        self.api_key = api_key
        if not mock_mode:
            try:
                from app.config import settings
                self.api_key = self.api_key or settings.OPENWEATHER_API_KEY
            except Exception:
                pass

    async def get_current(self, lat: float, lon: float) -> dict:
        """Get current weather for coordinates."""
        response = await self._make_request(
            "GET",
            f"{self.BASE_URL}/data/2.5/weather",
            params={"lat": lat, "lon": lon, "appid": self.api_key, "units": "metric", "lang": "fr"},
            _mock_key="current",
            _lat=lat,
            _lon=lon,
        )
        weather = response.get("weather", [{}])[0]
        main = response.get("main", {})
        wind = response.get("wind", {})
        clouds = response.get("clouds", {})
        sys = response.get("sys", {})

        return {
            "temp_celsius": main.get("temp", 12.0),
            "feels_like": main.get("feels_like", 10.0),
            "humidity": main.get("humidity", 65),
            "description": weather.get("description", "nuageux"),
            "wind_speed": wind.get("speed", 3.5),
            "clouds_pct": clouds.get("all", 50),
            "sunrise": sys.get("sunrise"),
            "sunset": sys.get("sunset"),
        }

    async def get_forecast_48h(self, lat: float, lon: float) -> list[dict]:
        """Get 48h forecast in 3h intervals."""
        response = await self._make_request(
            "GET",
            f"{self.BASE_URL}/data/2.5/forecast",
            params={"lat": lat, "lon": lon, "appid": self.api_key, "units": "metric", "lang": "fr"},
            _mock_key="forecast",
            _lat=lat,
            _lon=lon,
        )
        forecasts = []
        for item in response.get("list", [])[:16]:  # 16 x 3h = 48h
            weather = item.get("weather", [{}])[0]
            main = item.get("main", {})
            forecasts.append({
                "time": item.get("dt_txt", ""),
                "temp_celsius": main.get("temp", 12.0),
                "feels_like": main.get("feels_like", 10.0),
                "humidity": main.get("humidity", 65),
                "description": weather.get("description", "nuageux"),
                "clouds_pct": item.get("clouds", {}).get("all", 50),
                "wind_speed": item.get("wind", {}).get("speed", 3.5),
                "rain_mm": item.get("rain", {}).get("3h", 0),
            })
        return forecasts

    def _mock_response(self, method: str, url: str, **kwargs) -> dict:
        mock_key = kwargs.pop("_mock_key", "")
        now = datetime.now()
        month = now.month

        # Seasonal temperature ranges for France
        if month in (12, 1, 2):
            base_temp = random.uniform(2, 8)
        elif month in (3, 4, 5):
            base_temp = random.uniform(10, 18)
        elif month in (6, 7, 8):
            base_temp = random.uniform(22, 32)
        else:
            base_temp = random.uniform(12, 20)

        if mock_key == "current":
            return {
                "weather": [{"description": "partiellement nuageux", "icon": "02d"}],
                "main": {
                    "temp": round(base_temp, 1),
                    "feels_like": round(base_temp - 2, 1),
                    "humidity": random.randint(40, 80),
                    "pressure": 1013,
                },
                "wind": {"speed": round(random.uniform(1, 8), 1)},
                "clouds": {"all": random.randint(20, 80)},
                "sys": {
                    "sunrise": int((now.replace(hour=7, minute=30)).timestamp()),
                    "sunset": int((now.replace(hour=18, minute=0)).timestamp()),
                },
            }

        if mock_key == "forecast":
            items = []
            for i in range(16):
                forecast_time = now + timedelta(hours=i * 3)
                hour = forecast_time.hour
                # Temperature variation: cooler at night, warmer midday
                hour_offset = -3 if hour < 6 or hour > 20 else (3 if 11 <= hour <= 15 else 0)
                temp = round(base_temp + hour_offset + random.uniform(-1, 1), 1)
                items.append({
                    "dt_txt": forecast_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "weather": [{"description": random.choice(["ensoleillé", "nuageux", "partiellement nuageux"])}],
                    "main": {
                        "temp": temp,
                        "feels_like": round(temp - 2, 1),
                        "humidity": random.randint(40, 80),
                    },
                    "clouds": {"all": random.randint(10, 90)},
                    "wind": {"speed": round(random.uniform(1, 8), 1)},
                    "rain": {"3h": round(random.uniform(0, 2), 1) if random.random() > 0.7 else 0},
                })
            return {"list": items}

        return {}
