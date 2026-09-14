from __future__ import annotations

import os
from contextlib import asynccontextmanager
from dataclasses import asdict
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from urban_resilience_twin.domain.models import (
    Coordinate,
    Disruption,
    DisruptionKind,
    RoutePreferences,
    Scenario,
)
from urban_resilience_twin.ingestion.weather import OpenMeteoWeatherClient
from urban_resilience_twin.persistence.fuseki import FusekiClient
from urban_resilience_twin.routing.router import RouteNotFoundError
from urban_resilience_twin.semantic.validation import validate_graph

from .runtime import load_service_from_environment
from .schemas import AccessibilityRequest, RouteRequest, RouteResponse, ScenarioRequest
from .service import TwinService

SHAPES_PATH = Path(__file__).resolve().parents[1] / "semantic" / "shapes.ttl"


async def _publish_if_configured(app: FastAPI) -> None:
    client: FusekiClient | None = getattr(app.state, "fuseki", None)
    if client is None:
        return
    twin: TwinService = app.state.twin
    conforms, report = validate_graph(twin.semantic_graph, SHAPES_PATH)
    if not conforms:
        raise RuntimeError(f"Semantic graph failed SHACL validation:\n{report}")
    await client.publish_turtle(
        twin.semantic_graph.serialize(format="turtle"),
        graph_uri="https://example.org/berlin-resilience/runtime",
    )


def create_app(service: TwinService | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.twin = service or load_service_from_environment()
        app.state.weather = OpenMeteoWeatherClient()
        fuseki_url = os.getenv("FUSEKI_URL")
        app.state.fuseki = FusekiClient(fuseki_url) if fuseki_url else None
        if app.state.fuseki:
            await _publish_if_configured(app)
        yield

    app = FastAPI(
        title="Berlin Urban Resilience Twin API",
        version="1.0.0",
        description="Explainable urban accessibility, disruption and routing decision support.",
        lifespan=lifespan,
    )
    if service is not None:
        app.state.twin = service
        app.state.weather = OpenMeteoWeatherClient()
        app.state.fuseki = None

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:8080"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "version": "1.0.0"}

    @app.get("/ready")
    async def ready() -> dict:
        twin: TwinService = app.state.twin
        fuseki: FusekiClient | None = app.state.fuseki
        fuseki_ready = await fuseki.ready() if fuseki else None
        if fuseki is not None and not fuseki_ready:
            raise HTTPException(status_code=503, detail="Fuseki is not ready")
        return {"status": "ready", "data_mode": twin.data_mode, "fuseki_ready": fuseki_ready}

    @app.get("/facilities")
    def facilities() -> list[dict]:
        twin: TwinService = app.state.twin
        return [asdict(item) for item in twin.facilities]

    @app.get("/facilities/{facility_id}")
    def facility(facility_id: str) -> dict:
        twin: TwinService = app.state.twin
        item = next((f for f in twin.facilities if f.id == facility_id), None)
        if item is None:
            raise HTTPException(status_code=404, detail="Facility not found")
        return asdict(item)

    @app.get("/network/status")
    def network_status() -> dict:
        return app.state.twin.network_status()

    @app.get("/network/segments")
    def network_segments() -> dict:
        return app.state.twin.network_geojson()

    @app.get("/data/freshness")
    def data_freshness() -> dict:
        twin: TwinService = app.state.twin
        return {
            "road_network": {
                "mode": twin.data_mode,
                "policy": "snapshot; refresh explicitly with scripts/ingest_osm.py",
            },
            "weather": {
                "source": "Open-Meteo",
                "maximum_expected_age_minutes": 120,
                "loaded_on_demand": True,
            },
        }

    @app.get("/environment/weather")
    async def weather(latitude: float = 52.52, longitude: float = 13.405) -> dict:
        client: OpenMeteoWeatherClient = app.state.weather
        observation = await client.current(Coordinate(latitude, longitude))
        return asdict(observation)

    @app.get("/disruptions")
    def disruptions() -> list[dict]:
        twin: TwinService = app.state.twin
        return [
            asdict(disruption)
            for scenario in twin.scenarios.values()
            for disruption in scenario.disruptions
        ]

    @app.post("/scenario")
    async def create_scenario(request: ScenarioRequest) -> dict:
        twin: TwinService = app.state.twin
        scenario = Scenario(
            id=request.id,
            name=request.name,
            description=request.description,
            disruptions=tuple(
                Disruption(
                    id=item.id,
                    kind=DisruptionKind(item.kind),
                    affected_segment_ids=tuple(item.affected_segment_ids),
                    affected_district_ids=tuple(item.affected_district_ids),
                    penalty_seconds=item.penalty_seconds,
                    source_uri=item.source_uri,
                )
                for item in request.disruptions
            ),
        )
        twin.add_scenario(scenario, activate=request.activate)
        await _publish_if_configured(app)
        return {"id": scenario.id, "active": twin.active_scenario_id == scenario.id}

    @app.post("/route", response_model=RouteResponse)
    async def route(request: RouteRequest) -> RouteResponse:
        twin: TwinService = app.state.twin
        try:
            result = twin.route(
                Coordinate(request.origin.latitude, request.origin.longitude),
                Coordinate(request.destination.latitude, request.destination.longitude),
                request.mode,
                RoutePreferences(
                    disruption_weight=request.preferences.disruption_weight,
                    pollution_weight=request.preferences.pollution_weight,
                    reliability_weight=request.preferences.reliability_weight,
                ),
                request.scenario_id,
            )
        except RouteNotFoundError as exc:
            raise HTTPException(status_code=409, detail="No route available") from exc
        await _publish_if_configured(app)
        return RouteResponse(
            path_node_ids=list(result.path_node_ids),
            segment_ids=list(result.segment_ids),
            geometry=twin.geometry_for_path(result.path_node_ids),
            distance_m=result.distance_m,
            travel_time_s=result.travel_time_s,
            generalized_cost=result.generalized_cost,
            affected_segment_ids=list(result.affected_segment_ids),
            pollution_exposure=result.pollution_exposure,
            mean_reliability=result.mean_reliability,
            explanation=result.explanation,
        )

    @app.post("/analysis/accessibility")
    async def accessibility(request: AccessibilityRequest) -> dict:
        twin: TwinService = app.state.twin
        result = twin.accessibility_metrics(
            Coordinate(request.origin.latitude, request.origin.longitude),
            request.threshold_minutes * 60.0,
            request.scenario_id,
        )
        await _publish_if_configured(app)
        return asdict(result)

    @app.get("/analysis/scenario-comparison")
    def scenario_comparison(
        scenario_id: str,
        latitude: float = 52.52,
        longitude: float = 13.405,
        threshold_minutes: float = Query(default=15, gt=0, le=180),
    ) -> dict:
        twin: TwinService = app.state.twin
        if scenario_id not in twin.scenarios:
            raise HTTPException(status_code=404, detail="Scenario not found")
        return asdict(
            twin.scenario_comparison(
                Coordinate(latitude, longitude), threshold_minutes * 60.0, scenario_id
            )
        )

    @app.get("/analysis/critical-segments")
    def critical_segments(
        latitude: float = 52.52,
        longitude: float = 13.405,
        candidate_segment_id: Annotated[list[str] | None, Query()] = None,
    ) -> list[dict]:
        twin: TwinService = app.state.twin
        try:
            values = twin.critical_segments(
                Coordinate(latitude, longitude),
                tuple(candidate_segment_id) if candidate_segment_id else None,
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return [asdict(value) for value in values]

    @app.get("/analysis/unreachable-facilities")
    def unreachable_facilities(
        latitude: float = 52.52,
        longitude: float = 13.405,
        threshold_minutes: float = Query(default=15, gt=0, le=180),
    ) -> list[str]:
        twin: TwinService = app.state.twin
        metrics = twin.accessibility_metrics(
            Coordinate(latitude, longitude), threshold_minutes * 60.0, None
        )
        return list(metrics.unreachable_facility_ids)

    @app.get("/provenance")
    def provenance() -> dict:
        return app.state.twin.provenance_summary()

    @app.get("/graph")
    def graph_summary() -> dict:
        return app.state.twin.graph_summary()

    return app


app = create_app()
