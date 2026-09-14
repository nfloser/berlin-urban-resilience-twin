from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class FacilityType(StrEnum):
    HOSPITAL = "hospital"
    FIRE_STATION = "fire_station"
    EMERGENCY_SERVICE = "emergency_service"
    SHELTER = "shelter"


class RouteMode(StrEnum):
    FASTEST = "fastest"
    MOST_RELIABLE = "most_reliable"
    LOWEST_EXPOSURE = "lowest_exposure"
    DISRUPTION_AVOIDING = "disruption_avoiding"


class DisruptionKind(StrEnum):
    ROAD_CLOSURE = "road_closure"
    ROAD_PENALTY = "road_penalty"
    SEVERE_WEATHER = "severe_weather"
    HIGH_POLLUTION = "high_pollution"


@dataclass(frozen=True, slots=True)
class Coordinate:
    latitude: float
    longitude: float


@dataclass(frozen=True, slots=True)
class District:
    id: str
    name: str


@dataclass(frozen=True, slots=True)
class RoadNode:
    id: str
    coordinate: Coordinate


@dataclass(frozen=True, slots=True)
class RoadSegment:
    id: str
    start_node_id: str
    end_node_id: str
    length_m: float
    travel_time_s: float
    reliability: float = 1.0
    pollution_exposure: float = 0.0
    source_uri: str | None = None


@dataclass(frozen=True, slots=True)
class Facility:
    id: str
    name: str
    facility_type: FacilityType
    coordinate: Coordinate
    district_id: str
    connected_node_id: str
    source_uri: str | None = None


@dataclass(frozen=True, slots=True)
class Disruption:
    id: str
    kind: DisruptionKind
    affected_segment_ids: tuple[str, ...] = ()
    affected_district_ids: tuple[str, ...] = ()
    penalty_seconds: float = 0.0
    starts_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    ends_at: datetime | None = None
    source_uri: str | None = None

    @property
    def closes_segments(self) -> bool:
        return self.kind == DisruptionKind.ROAD_CLOSURE


@dataclass(frozen=True, slots=True)
class Scenario:
    id: str
    name: str
    disruptions: tuple[Disruption, ...]
    description: str = ""


@dataclass(frozen=True, slots=True)
class RoutePreferences:
    disruption_weight: float = 1.0
    pollution_weight: float = 0.0
    reliability_weight: float = 0.0


@dataclass(frozen=True, slots=True)
class RouteResult:
    path_node_ids: tuple[str, ...]
    segment_ids: tuple[str, ...]
    distance_m: float
    travel_time_s: float
    generalized_cost: float
    affected_segment_ids: tuple[str, ...]
    pollution_exposure: float
    mean_reliability: float
    explanation: str


@dataclass(frozen=True, slots=True)
class AccessibilityMetrics:
    origin_node_id: str
    threshold_s: float
    reachable_facility_ids: tuple[str, ...]
    unreachable_facility_ids: tuple[str, ...]
    nearest_facility_id: str | None
    nearest_facility_travel_time_s: float | None
    median_facility_travel_time_s: float | None


@dataclass(frozen=True, slots=True)
class ScenarioComparison:
    baseline: AccessibilityMetrics
    disrupted: AccessibilityMetrics
    reachable_facility_change: int
    median_travel_time_change_s: float | None
    facilities_becoming_unreachable: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SegmentImpact:
    segment_id: str
    baseline_nearest_facility_s: float | None
    disrupted_nearest_facility_s: float | None
    increase_s: float | None
    disconnects_all_facilities: bool


@dataclass(frozen=True, slots=True)
class WeatherObservation:
    observed_at: datetime
    coordinate: Coordinate
    rain_mm: float
    precipitation_mm: float
    wind_speed_kmh: float
    weather_code: int | None
    source_uri: str
