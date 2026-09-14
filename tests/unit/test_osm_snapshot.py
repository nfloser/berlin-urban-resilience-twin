from pathlib import Path

from urban_resilience_twin.domain.models import Coordinate, RoadNode, RoadSegment
from urban_resilience_twin.domain.network import TransportNetwork
from urban_resilience_twin.ingestion.osm import load_network_json, write_network_json


def test_normalized_osm_snapshot_round_trip(tmp_path: Path) -> None:
    network = TransportNetwork()
    network.add_node(RoadNode("1", Coordinate(52.52, 13.4)))
    network.add_node(RoadNode("2", Coordinate(52.53, 13.41)))
    network.add_segment(
        RoadSegment(
            "s",
            "1",
            "2",
            120,
            12,
            source_uri="https://www.openstreetmap.org/way/1",
        )
    )
    path = write_network_json(network, tmp_path / "network.json")
    loaded = load_network_json(path)
    assert loaded.graph.edges["1", "2"]["travel_time_s"] == 12
    assert loaded.graph.edges["1", "2"]["source_uri"].endswith("/1")
