from urban_resilience_twin.analysis.accessibility import AccessibilityAnalyzer
from urban_resilience_twin.domain.models import (
    Coordinate,
    Disruption,
    DisruptionKind,
    Facility,
    FacilityType,
    RoadNode,
    RoadSegment,
    Scenario,
)
from urban_resilience_twin.domain.network import TransportNetwork


def test_accessibility_comparison_reports_hospital_becoming_unreachable() -> None:
    network = TransportNetwork()
    network.add_node(RoadNode("A", Coordinate(52, 13)))
    network.add_node(RoadNode("B", Coordinate(52, 13.01)))
    network.add_segment(RoadSegment("AB", "A", "B", 100, 300))
    hospital = Facility(
        "H", "Hospital", FacilityType.HOSPITAL, Coordinate(52, 13.01), "D", "B"
    )
    scenario = Scenario(
        "s", "closure", (Disruption("d", DisruptionKind.ROAD_CLOSURE, ("AB",)),)
    )
    comparison = AccessibilityAnalyzer().compare(network, "A", [hospital], 900, scenario)
    assert comparison.baseline.reachable_facility_ids == ("H",)
    assert comparison.disrupted.unreachable_facility_ids == ("H",)
    assert comparison.facilities_becoming_unreachable == ("H",)
