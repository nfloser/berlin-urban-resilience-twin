import networkx as nx

from urban_resilience_twin.ingestion.osm import OSMNetworkMapper


def test_osm_mapping_converts_realistic_multidigraph_attributes() -> None:
    graph = nx.MultiDiGraph()
    graph.add_node(1, x=13.4, y=52.52)
    graph.add_node(2, x=13.41, y=52.53)
    graph.add_edge(1, 2, key=0, osmid=123, length=100.0, maxspeed="50", highway="primary")
    mapped = OSMNetworkMapper().map_graph(graph)
    assert mapped.graph.number_of_edges() == 1
    edge = mapped.graph.edges["1", "2"]
    assert edge["segment_id"].startswith("osm-way-123")
    assert edge["travel_time_s"] == 7.2
