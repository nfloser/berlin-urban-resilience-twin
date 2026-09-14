from urban_resilience_twin.domain.models import (
    Coordinate,
    Disruption,
    DisruptionKind,
    RoadNode,
    RoadSegment,
    RouteMode,
    RoutePreferences,
    Scenario,
)
from urban_resilience_twin.domain.network import TransportNetwork
from urban_resilience_twin.routing.router import Router


def network() -> TransportNetwork:
    graph = TransportNetwork()
    for node_id, lon in (("A", 13.0), ("B", 13.01), ("C", 13.02)):
        graph.add_node(RoadNode(node_id, Coordinate(52.0, lon)))
    graph.add_segment(RoadSegment("AB", "A", "B", 5, 5, reliability=0.99, pollution_exposure=2))
    graph.add_segment(RoadSegment("BC", "B", "C", 5, 5, reliability=0.99, pollution_exposure=2))
    graph.add_segment(RoadSegment("AC", "A", "C", 20, 20, reliability=1.0, pollution_exposure=0.1))
    return graph


def test_dijkstra_selects_ab_c_on_toy_graph() -> None:
    result = Router().route(network(), "A", "C")
    assert result.path_node_ids == ("A", "B", "C")
    assert result.travel_time_s == 10


def test_road_closure_changes_route_without_mutating_base() -> None:
    base = network()
    scenario = Scenario(
        "closure",
        "Close BC",
        (Disruption("d1", DisruptionKind.ROAD_CLOSURE, affected_segment_ids=("BC",)),),
    )
    result = Router().route(base, "A", "C", scenario=scenario)
    assert result.path_node_ids == ("A", "C")
    assert base.graph.has_edge("B", "C")


def test_lowest_exposure_uses_explicit_user_weight() -> None:
    result = Router().route(
        network(),
        "A",
        "C",
        mode=RouteMode.LOWEST_EXPOSURE,
        preferences=RoutePreferences(pollution_weight=100),
    )
    assert result.path_node_ids == ("A", "C")
