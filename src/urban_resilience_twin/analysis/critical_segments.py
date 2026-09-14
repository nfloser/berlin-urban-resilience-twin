from __future__ import annotations

import networkx as nx

from urban_resilience_twin.domain.models import Facility, SegmentImpact
from urban_resilience_twin.domain.network import TransportNetwork


def _nearest_time(graph: nx.Graph, origin: str, facilities: list[Facility]) -> float | None:
    lengths = nx.single_source_dijkstra_path_length(graph, origin, weight="travel_time_s")
    values = [lengths[f.connected_node_id] for f in facilities if f.connected_node_id in lengths]
    return min(values) if values else None


def critical_segment_impacts(
    network: TransportNetwork,
    origin_node_id: str,
    facilities: list[Facility],
    candidate_segment_ids: tuple[str, ...] | None = None,
) -> list[SegmentImpact]:
    baseline = _nearest_time(network.graph, origin_node_id, facilities)
    candidates = candidate_segment_ids or network.segment_ids()
    results: list[SegmentImpact] = []
    for segment_id in candidates:
        endpoints = network.segment_endpoints(segment_id)
        if endpoints is None or not network.graph.has_edge(*endpoints):
            continue
        graph = network.graph.copy()
        graph.remove_edge(*endpoints)
        disrupted = _nearest_time(graph, origin_node_id, facilities)
        increase = None if baseline is None or disrupted is None else float(disrupted - baseline)
        results.append(
            SegmentImpact(
                segment_id=segment_id,
                baseline_nearest_facility_s=baseline,
                disrupted_nearest_facility_s=disrupted,
                increase_s=increase,
                disconnects_all_facilities=disrupted is None,
            )
        )
    return sorted(
        results,
        key=lambda item: (
            item.disconnects_all_facilities,
            item.increase_s if item.increase_s is not None else float("inf"),
        ),
        reverse=True,
    )
