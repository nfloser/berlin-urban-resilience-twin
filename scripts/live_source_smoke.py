from __future__ import annotations

import asyncio

from urban_resilience_twin.domain.models import Coordinate
from urban_resilience_twin.ingestion.weather import OpenMeteoWeatherClient


def check_osm() -> None:
    import osmnx as ox

    graph = ox.graph.graph_from_point((52.5200, 13.4050), dist=500, network_type="drive")
    if graph.number_of_nodes() < 2 or graph.number_of_edges() < 1:
        raise RuntimeError("OpenStreetMap smoke query returned no usable road network")


async def check_weather() -> None:
    observation = await OpenMeteoWeatherClient().current(Coordinate(52.5200, 13.4050))
    if observation.source_uri == "" or observation.observed_at is None:
        raise RuntimeError("Weather source did not return a timestamped observation")


def main() -> None:
    check_osm()
    asyncio.run(check_weather())
    print("live source smoke test passed")


if __name__ == "__main__":
    main()
