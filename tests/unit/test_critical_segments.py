from urban_resilience_twin.analysis.critical_segments import critical_segment_impacts
from urban_resilience_twin.domain.models import (
    Coordinate,
    Facility,
    FacilityType,
    RoadNode,
    RoadSegment,
)
from urban_resilience_twin.domain.network import TransportNetwork


def test_bridge_segment_is_identified_as_disconnective() -> None:
    network = TransportNetwork()
    for node_id, lon in (("A", 13.0), ("B", 13.01), ("H", 13.02)):
        network.add_node(RoadNode(node_id, Coordinate(52, lon)))
    network.add_segment(RoadSegment("AB", "A", "B", 100, 10))
    network.add_segment(RoadSegment("BH", "B", "H", 100, 10))
    facility = Facility(
        "hospital", "Hospital", FacilityType.HOSPITAL, Coordinate(52, 13.02), "D", "H"
    )
    impacts = critical_segment_impacts(network, "A", [facility])
    by_id = {item.segment_id: item for item in impacts}
    assert by_id["AB"].disconnects_all_facilities is True
    assert by_id["BH"].disconnects_all_facilities is True
