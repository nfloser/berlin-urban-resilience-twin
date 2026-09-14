from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from urban_resilience_twin.domain.models import RouteMode


class CoordinateSchema(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class RoutePreferencesSchema(BaseModel):
    disruption_weight: float = Field(default=1.0, ge=0)
    pollution_weight: float = Field(default=0.0, ge=0)
    reliability_weight: float = Field(default=0.0, ge=0)


class RouteRequest(BaseModel):
    origin: CoordinateSchema
    destination: CoordinateSchema
    mode: RouteMode = RouteMode.FASTEST
    preferences: RoutePreferencesSchema = Field(default_factory=RoutePreferencesSchema)
    scenario_id: str | None = None


class RouteResponse(BaseModel):
    path_node_ids: list[str]
    segment_ids: list[str]
    geometry: list[list[float]]
    distance_m: float
    travel_time_s: float
    generalized_cost: float
    affected_segment_ids: list[str]
    pollution_exposure: float
    mean_reliability: float
    explanation: str


class DisruptionSchema(BaseModel):
    id: str
    kind: Literal["road_closure", "road_penalty", "severe_weather", "high_pollution"]
    affected_segment_ids: list[str] = Field(default_factory=list)
    affected_district_ids: list[str] = Field(default_factory=list)
    penalty_seconds: float = Field(default=0, ge=0)
    source_uri: str | None = None


class ScenarioRequest(BaseModel):
    id: str
    name: str
    description: str = ""
    disruptions: list[DisruptionSchema]
    activate: bool = True


class AccessibilityRequest(BaseModel):
    origin: CoordinateSchema
    threshold_minutes: float = Field(default=15, gt=0, le=180)
    scenario_id: str | None = None
