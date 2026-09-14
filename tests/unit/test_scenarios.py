from urban_resilience_twin.domain.models import (
    Coordinate,
    Disruption,
    DisruptionKind,
    RoadNode,
    RoadSegment,
    Scenario,
)
from urban_resilience_twin.domain.network import TransportNetwork
from urban_resilience_twin.scenarios.engine import ScenarioEngine


def test_overlay_penalises_edge_but_preserves_base() -> None:
    base = TransportNetwork()
    base.add_node(RoadNode("A", Coordinate(52, 13)))
    base.add_node(RoadNode("B", Coordinate(52, 13.01)))
    base.add_segment(RoadSegment("AB", "A", "B", 100, 10))
    scenario = Scenario(
        "rain",
        "Heavy rain",
        (Disruption("wet", DisruptionKind.ROAD_PENALTY, ("AB",), penalty_seconds=30),),
    )
    derived = ScenarioEngine().derive_network(base, scenario)
    assert derived.graph.edges["A", "B"]["scenario_penalty_s"] == 30
    assert base.graph.edges["A", "B"]["scenario_penalty_s"] == 0
