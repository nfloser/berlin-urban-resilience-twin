from pathlib import Path

import pytest
from rdflib import Graph

from urban_resilience_twin.domain.models import (
    Coordinate,
    Disruption,
    DisruptionKind,
    District,
    Facility,
    FacilityType,
    RoadNode,
    RoadSegment,
    Scenario,
)
from urban_resilience_twin.semantic.mapper import (
    add_disruption,
    add_district,
    add_facility,
    add_road_node,
    add_road_segment,
    add_scenario,
)
from urban_resilience_twin.semantic.queries import (
    facilities_connected_through_disrupted_segments,
    hospitals_in_affected_districts,
)
from urban_resilience_twin.semantic.validation import validate_graph


def populated_graph() -> Graph:
    graph = Graph()
    add_district(graph, District("mitte", "Mitte"))
    add_road_node(graph, RoadNode("A", Coordinate(52.52, 13.4)))
    add_road_node(graph, RoadNode("B", Coordinate(52.53, 13.41)))
    add_road_segment(graph, RoadSegment("AB", "A", "B", 100, 10))
    add_facility(
        graph,
        Facility(
            "H",
            "Hospital",
            FacilityType.HOSPITAL,
            Coordinate(52.52, 13.4),
            "mitte",
            "A",
        ),
    )
    add_disruption(graph, Disruption("storm", DisruptionKind.SEVERE_WEATHER, ("AB",), ("mitte",)))
    return graph


def test_sparql_cross_domain_queries_require_linked_relationships() -> None:
    graph = populated_graph()
    assert hospitals_in_affected_districts(graph)
    assert facilities_connected_through_disrupted_segments(graph)


def test_shacl_accepts_valid_semantic_state() -> None:
    pytest.importorskip("pyshacl")
    graph = populated_graph()
    shapes = Path(__file__).parents[2] / "src/urban_resilience_twin/semantic/shapes.ttl"
    conforms, report = validate_graph(graph, shapes)
    assert conforms, report


def test_scenario_links_to_its_disruptions() -> None:
    graph = Graph()
    disruption = Disruption("closure", DisruptionKind.ROAD_CLOSURE, ("AB",))
    scenario = Scenario("rain", "Heavy rain", (disruption,))
    add_scenario(graph, scenario)
    pairs = list(
        graph.query(
            """
            PREFIX urt: <https://example.org/berlin-resilience/>
            SELECT ?scenario ?event WHERE {
              ?scenario a urt:Scenario ; urt:includesDisruption ?event .
              ?event a urt:Disruption .
            }
            """
        )
    )
    assert len(pairs) == 1
