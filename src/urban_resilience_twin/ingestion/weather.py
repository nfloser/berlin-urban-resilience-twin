from __future__ import annotations

from datetime import datetime

import httpx

from urban_resilience_twin.domain.models import Coordinate, WeatherObservation

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


class OpenMeteoWeatherClient:
    def __init__(self, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self.transport = transport

    async def current(self, coordinate: Coordinate) -> WeatherObservation:
        params = {
            "latitude": coordinate.latitude,
            "longitude": coordinate.longitude,
            "current": "rain,precipitation,weather_code,wind_speed_10m",
            "timezone": "UTC",
        }
        async with httpx.AsyncClient(transport=self.transport, timeout=10.0) as client:
            response = await client.get(OPEN_METEO_URL, params=params)
            response.raise_for_status()
            payload = response.json()["current"]
        observed_at = datetime.fromisoformat(str(payload["time"]).replace("Z", "+00:00"))
        return WeatherObservation(
            observed_at=observed_at,
            coordinate=coordinate,
            rain_mm=float(payload.get("rain", 0.0)),
            precipitation_mm=float(payload.get("precipitation", 0.0)),
            wind_speed_kmh=float(payload.get("wind_speed_10m", 0.0)),
            weather_code=(
                int(payload["weather_code"])
                if payload.get("weather_code") is not None
                else None
            ),
            source_uri=OPEN_METEO_URL,
        )
