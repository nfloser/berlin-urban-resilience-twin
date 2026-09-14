import httpx
import pytest

from urban_resilience_twin.domain.models import Coordinate
from urban_resilience_twin.ingestion.weather import OpenMeteoWeatherClient


@pytest.mark.asyncio
async def test_weather_client_maps_current_observation() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "current": {
                    "time": "2026-09-14T10:00Z",
                    "rain": 1.2,
                    "precipitation": 1.4,
                    "weather_code": 63,
                    "wind_speed_10m": 28.0,
                }
            },
        )

    client = OpenMeteoWeatherClient(httpx.MockTransport(handler))
    value = await client.current(Coordinate(52.52, 13.405))
    assert value.rain_mm == 1.2
    assert value.wind_speed_kmh == 28.0
