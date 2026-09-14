from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from rdflib import Graph

from urban_resilience_twin.analysis.accessibility import AccessibilityAnalyzer
from urban_resilience_twin.analysis.critical_segments import critical_segment_impacts
from urban_resilience_twin.domain.models import (
    Coordinate,
    District,
    Facility,
    FacilityType,
    RoadNode,
    RoadSegment,
    RouteMode,
    RoutePreferences,
    Scenario,
)
from urban_resilience_twin.domain.network import TransportNetwork
from urban_resilience_twin.routing.router import Router
from urban_resilience_twin.semantic.mapper import (
    add_analysis_provenance,
    add_district,
    add_facility,
    add_road_node,
    add_road_segment,
    add_route_provenance,
    add_scenario,
)


class TwinService:
    def __init__(
        self,
        network: TransportNetwork,
        facilities: list[Facility],
        districts: list[District],
        data_mode: str,
    ) -> None:
        self.network = network
        self.facilities = facilities
        self.districts = districts
        self.data_mode = data_mode
        self.router = Router()
        self.accessibility = AccessibilityAnalyzer()
        self.scenarios: dict[str, Scenario] = {}
        self.active_scenario_id: str | None = None
        self.semantic_graph = Graph()
        self.started_at = datetime.now(UTC)
        for district in districts:
            add_district(self.semantic_graph, district)
        for node_id, data in network.graph.nodes(data=True):
            add_road_node(
                self.semantic_graph,
                RoadNode(
                    id=str(node_id),
                    coordinate=Coordinate(data["latitude"], data["longitude"]),
                ),
            )
        for u, v, data in network.graph.edges(data=True):
            add_road_segment(
                self.semantic_graph,
                RoadSegment(
                    id=str(data["segment_id"]),
                    start_node_id=str(u),
                    end_node_id=str(v),
                    length_m=float(data["length_m"]),
                    travel_time_s=float(data["travel_time_s"]),
                    reliability=float(data.get("reliability", 1.0)),
                    pollution_exposure=float(data.get("pollution_exposure", 0.0)),
                    source_uri=data.get("source_uri"),
                ),
            )
        for facility in facilities:
            add_facility(self.semantic_graph, facility)

    @property
    def active_scenario(self) -> Scenario | None:
        return self.scenarios.get(self.active_scenario_id) if self.active_scenario_id else None

    def add_scenario(self, scenario: Scenario, activate: bool = True) -> None:
        self.scenarios[scenario.id] = scenario
        if activate:
            self.active_scenario_id = scenario.id
        add_scenario(self.semantic_graph, scenario)

    def route(
        self,
        origin: Coordinate,
        destination: Coordinate,
        mode: RouteMode,
        preferences: RoutePreferences,
        scenario_id: str | None,
    ):
        origin_node = self.network.nearest_node(origin)
        destination_node = self.network.nearest_node(destination)
        scenario = self.scenarios.get(scenario_id) if scenario_id else self.active_scenario
        result = self.router.route(
            self.network,
            origin_node,
            destination_node,
            mode=mode,
            preferences=preferences,
            scenario=scenario,
        )
        result_id = f"route-{uuid4()}"
        source_ids = ("road-network",) + ((f"scenario:{scenario.id}",) if scenario else ())
        add_route_provenance(
            self.semantic_graph,
            result_id,
            source_ids,
            origin_node,
            destination_node,
            mode,
        )
        return result

    def geometry_for_path(self, path: tuple[str, ...]) -> list[list[float]]:
        return [
            [
                float(self.network.graph.nodes[node_id]["longitude"]),
                float(self.network.graph.nodes[node_id]["latitude"]),
            ]
            for node_id in path
        ]

    def accessibility_metrics(
        self, origin: Coordinate, threshold_s: float, scenario_id: str | None
    ):
        origin_node = self.network.nearest_node(origin)
        scenario = self.scenarios.get(scenario_id) if scenario_id else self.active_scenario
        result = self.accessibility.measure(
            self.network, origin_node, self.facilities, threshold_s, scenario
        )
        add_analysis_provenance(
            self.semantic_graph,
            f"accessibility-{uuid4()}",
            ("road-network",) + ((f"scenario:{scenario.id}",) if scenario else ()),
            "accessibility-analysis-agent",
        )
        return result

    def scenario_comparison(self, origin: Coordinate, threshold_s: float, scenario_id: str):
        origin_node = self.network.nearest_node(origin)
        scenario = self.scenarios[scenario_id]
        return self.accessibility.compare(
            self.network, origin_node, self.facilities, threshold_s, scenario
        )

    def critical_segments(
        self,
        origin: Coordinate,
        candidate_segment_ids: tuple[str, ...] | None = None,
    ):
        if candidate_segment_ids is None and self.network.graph.number_of_edges() > 500:
            raise ValueError(
                "Critical-segment analysis on networks above 500 edges requires explicit candidates"
            )
        origin_node = self.network.nearest_node(origin)
        return critical_segment_impacts(
            self.network, origin_node, self.facilities, candidate_segment_ids
        )

    def network_geojson(self) -> dict:
        affected = {
            segment_id
            for disruption in (self.active_scenario.disruptions if self.active_scenario else ())
            for segment_id in disruption.affected_segment_ids
        }
        features = []
        for u, v, data in self.network.graph.edges(data=True):
            start = self.network.graph.nodes[u]
            end = self.network.graph.nodes[v]
            segment_id = str(data["segment_id"])
            features.append(
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [
                            [float(start["longitude"]), float(start["latitude"])],
                            [float(end["longitude"]), float(end["latitude"])],
                        ],
                    },
                    "properties": {
                        "segment_id": segment_id,
                        "affected": segment_id in affected,
                        "travel_time_s": float(data["travel_time_s"]),
                    },
                }
            )
        return {"type": "FeatureCollection", "features": features}

    def network_status(self) -> dict:
        derived = self.router.scenario_engine.derive_network(self.network, self.active_scenario)
        baseline_edges = self.network.graph.number_of_edges()
        active_edges = derived.graph.number_of_edges()
        return {
            "data_mode": self.data_mode,
            "nodes": self.network.graph.number_of_nodes(),
            "baseline_segments": baseline_edges,
            "active_segments": active_edges,
            "disconnected_percentage": (
                0.0
                if baseline_edges == 0
                else (baseline_edges - active_edges) / baseline_edges * 100.0
            ),
            "active_scenario_id": self.active_scenario_id,
            "generated_at": datetime.now(UTC).isoformat(),
        }

    def provenance_summary(self) -> dict:
        return {
            "triple_count": len(self.semantic_graph),
            "turtle": self.semantic_graph.serialize(format="turtle"),
        }

    def graph_summary(self) -> dict:
        return {
            "nodes": self.network.graph.number_of_nodes(),
            "edges": self.network.graph.number_of_edges(),
            "facilities": len(self.facilities),
            "districts": len(self.districts),
            "semantic_triples": len(self.semantic_graph),
        }


def build_demo_service() -> TwinService:
    """Deterministic local/CI fixture, explicitly not production Berlin data."""
    network = TransportNetwork()
    coords = {
        "A": Coordinate(52.5200, 13.4050),
        "B": Coordinate(52.5220, 13.4100),
        "C": Coordinate(52.5240, 13.4150),
        "D": Coordinate(52.5180, 13.4140),
    }
    for node_id, coordinate in coords.items():
        network.add_node(RoadNode(node_id, coordinate))
    network.add_segment(RoadSegment("AB", "A", "B", 500, 300, 0.99, 2))
    network.add_segment(RoadSegment("BC", "B", "C", 500, 300, 0.98, 3))
    network.add_segment(RoadSegment("AD", "A", "D", 900, 420, 0.95, 1))
    network.add_segment(RoadSegment("DC", "D", "C", 900, 420, 0.95, 1))
    facilities = [
        Facility(
            id="demo-hospital-c",
            name="Demo Hospital (CI fixture)",
            facility_type=FacilityType.HOSPITAL,
            coordinate=coords["C"],
            district_id="demo-mitte",
            connected_node_id="C",
        )
    ]
    districts = [District(id="demo-mitte", name="Demo Mitte")]
    return TwinService(network, facilities, districts, data_mode="deterministic-fixture")
