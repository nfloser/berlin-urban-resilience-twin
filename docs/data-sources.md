# Data sources

## OpenStreetMap

Road topology and selected critical facilities are ingested with OSMnx from OpenStreetMap. The default real-data command targets `Mitte, Berlin, Germany` to keep the first research scope bounded.

Produced artifacts:

- `road-network.graphml`: raw OSMnx graph snapshot,
- `facilities.geojson`: raw selected OSM features,
- `network.json`: normalized runtime road topology,
- `facilities.json`: normalized facilities snapped to road nodes,
- `source-metadata.json`: source/query/attribution metadata.

The ingestion command does not run during deterministic CI. OpenStreetMap attribution must remain visible in any map or redistributed derivative dataset.

## Open-Meteo

The environmental client retrieves timestamped current rain, precipitation, weather code and 10 m wind speed for a coordinate. The API exposes a two-hour expected freshness policy. Weather data is contextual evidence only; v1 does not claim that a weather observation automatically proves a road is impassable.

## Source limitations

OpenStreetMap completeness is community-dependent. Critical-facility coverage is not guaranteed. OSM speed tags may be absent; the mapper then uses documented road-class fallback speeds for free-flow travel-time approximation. These fallback speeds are engineering assumptions, not observed traffic.
