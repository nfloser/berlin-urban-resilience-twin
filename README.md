# Berlin Urban Resilience Twin

A research-oriented semantic digital twin and decision-support system for analysing how urban disruptions change road accessibility to critical infrastructure in Berlin.

The project is intentionally more than a multi-layer map. It connects **real urban entities → semantic relationships → road-network topology → scenario disruptions → graph algorithms → measurable accessibility change → explainable route/decision support → an interactive map**.

## Research questions

- Which critical facilities become unreachable or slower to reach when road segments fail?
- Which road segments are structurally important for access to hospitals or emergency infrastructure?
- How does a disruption scenario change reachable facilities within a fixed travel-time budget?
- How does the fastest path differ from reliability-, disruption- or exposure-weighted alternatives?
- Which facilities and road components are semantically linked to an affected district or disruption?

## What v1 implements

- OpenStreetMap road/facility ingestion through OSMnx with normalized provenance-bearing snapshots.
- Open-Meteo current weather client with explicit freshness policy.
- NetworkX routing and accessibility analysis with deterministic toy-graph tests.
- Immutable scenario overlays for closures and penalties.
- Fastest, disruption-avoiding, most-reliable and lowest-exposure route objectives.
- Directly interpretable resilience metrics and single-segment sensitivity analysis.
- RDF mappings, application-level cross-domain SPARQL impact analysis, PROV-O provenance and SHACL validation.
- Persistent Apache Jena Fuseki/TDB2 semantic state in Docker.
- FastAPI decision-support API.
- React + TypeScript + MapLibre full-screen map with scenario and route controls.
- Deterministic CI plus a separate scheduled/manual live-source smoke workflow.

## Architecture

```text
                  real external sources
                OSM             Open-Meteo
                 |                  |
                 +------ ingestion--+
                           |
                 normalized snapshots
                           |
             +-------------+-------------+
             |                           |
        NetworkX graph                 RDF graph
   routing / scenarios /          entities / links /
 accessibility / sensitivity     SPARQL / provenance
             |                           |
             +-------------+-------------+
                           |
                        FastAPI
                           |
                React + MapLibre UI
                           |
                    decision support

RDF state --SHACL gate--> Apache Jena Fuseki / TDB2
```

The storage split is deliberate. NetworkX solves topology problems; Fuseki stores semantic identity, relationships and provenance. The knowledge graph is useful because application queries traverse those relationships instead of merely co-locating unrelated observations.

## Quick start: deterministic research fixture

The default Compose stack uses a tiny deterministic network so it is reproducible and independent of third-party services.

```bash
docker compose up --build
```

Open:

- frontend: `http://localhost:8080`
- API/OpenAPI: `http://localhost:8000/docs`
- Fuseki dataset: `http://localhost:3030/resilience`

The API reports `data_mode=deterministic-fixture` so this state cannot be confused with real Berlin data.

## Run with real Berlin OSM data

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[ingestion]"
python scripts/ingest_osm.py --place "Mitte, Berlin, Germany" --output data/generated
docker compose -f docker-compose.yml -f docker-compose.real.yml up --build
```

The runtime then reports `data_mode=osm-snapshot`. The ingestion stores both raw audit artifacts and lightweight normalized JSON used by the backend.

## TDD examples

The routing suite starts from a deterministic graph:

```text
A ----5---- B ----5---- C
 \                       /
  -----------20----------
```

Dijkstra must choose `A-B-C`. A closure on `BC` must force `A-C` while the base graph remains unchanged. Accessibility tests separately prove that a bridge closure can make a connected hospital unreachable.

## Route objectives

Multi-criteria objectives expose weights as user preferences rather than scientific constants. Generalized cost and physical travel time are returned separately. See [`docs/routing.md`](docs/routing.md).

## API

Core endpoints include:

```text
GET  /health
GET  /ready
GET  /facilities
GET  /network/status
GET  /data/freshness
GET  /environment/weather
GET  /disruptions
POST /scenario
POST /route
POST /analysis/accessibility
GET  /analysis/critical-segments
GET  /analysis/unreachable-facilities
GET  /analysis/semantic-impact
GET  /analysis/scenario-comparison
GET  /provenance
GET  /graph
```

Example route request:

```json
{
  "origin": {"latitude": 52.52, "longitude": 13.405},
  "destination": {"latitude": 52.50, "longitude": 13.39},
  "mode": "most_reliable",
  "preferences": {
    "disruption_weight": 2.0,
    "pollution_weight": 0.0,
    "reliability_weight": 1.5
  }
}
```

## Documentation

- [`docs/architecture.md`](docs/architecture.md)
- [`docs/data-sources.md`](docs/data-sources.md)
- [`docs/ontology.md`](docs/ontology.md)
- [`docs/routing.md`](docs/routing.md)
- [`docs/resilience-analysis.md`](docs/resilience-analysis.md)
- [`docs/scenarios.md`](docs/scenarios.md)
- [`docs/development.md`](docs/development.md)
- [`docs/limitations.md`](docs/limitations.md)
- [`docs/decisions/`](docs/decisions/)

## Scientific and operational boundaries

This repository does **not** claim real-time traffic-aware emergency routing, complete facility coverage, validated pollution exposure, or a scientifically universal resilience score. Weather observations are not automatically converted into closures. Historical mode is not exposed until a defensible historical dataset exists. See the limitations document before interpreting outputs.

## Data attribution

Road and facility data ingested by the project comes from © OpenStreetMap contributors. Environmental observations are retrieved from Open-Meteo. Source URLs and ingestion metadata are retained for traceability.

## License

MIT. Data obtained from external providers remains subject to the respective provider/source licenses and attribution requirements.
