# Architecture

## Goal

Network calculations, semantic relationships and geospatial source data use separate components instead of sharing one graph database.

```text
OpenStreetMap / Open-Meteo
          |
          v
 ingestion + provenance
          |
  +-------+---------+
  |                 |
  v                 v
NetworkX        RDF graph
routing /       entities / relations /
accessibility   scenarios / provenance
  |                 |
  +--------+--------+
           v
        FastAPI
           |
           v
 React + MapLibre decision-support UI
           |
           v
 Fuseki/TDB2 persistent semantic state
```

## Responsibility split

**NetworkX** owns topology-dependent computation: Dijkstra routing, connectivity, accessibility, scenario overlays and critical-segment sensitivity. The base graph is immutable from the scenario engine's point of view; scenarios are applied to copies.

**RDF/Fuseki** owns cross-domain identity, relationships, provenance and queryable semantic state. SHACL is a publication gate: invalid semantic state is rejected before it is written to the persistent store.

**Normalized JSON snapshots** are the boundary between heavyweight OSMnx ingestion and the lightweight runtime. Raw GraphML/GeoJSON may also be retained for audit, but the backend does not need GeoPandas or OSMnx to serve a previously ingested snapshot.

**FastAPI** exposes explicit schemas and keeps HTTP handlers thin. Computational behaviour lives in domain/analysis services.

**React + MapLibre** is the primary user interface. It visualizes facilities and routes, exposes scenario/routing preferences, and always presents an explanation alongside derived results.

## Data modes

The runtime exposes its current `data_mode`.

- `deterministic-fixture`: small synthetic network used for CI and local testing. It is never described as real Berlin data.
- `osm-snapshot`: a normalized snapshot produced from real OpenStreetMap data by `scripts/ingest_osm.py`.

The exposed data mode lets clients distinguish test fixtures from real OSM snapshots.
