from __future__ import annotations

import math

import networkx as nx

from .models import Coordinate, RoadNode, RoadSegment


class TransportNetwork:
    """Thin domain wrapper around a directed NetworkX graph."""

    def __init__(self) -> None:
        self.graph = nx.DiGraph()
        self._segments: dict[str, tuple[str, str]] = {}

    def copy(self) -> TransportNetwork:
        copied = TransportNetwork()
        copied.graph = self.graph.copy()
        copied._segments = self._segments.copy()
        return copied

    def add_node(self, node: RoadNode) -> None:
        self.graph.add_node(
            node.id,
            latitude=node.coordinate.latitude,
            longitude=node.coordinate.longitude,
        )

    def add_segment(self, segment: RoadSegment) -> None:
        if segment.start_node_id not in self.graph or segment.end_node_id not in self.graph:
            raise ValueError("Both segment endpoints must exist before adding a segment")
        if not 0.0 <= segment.reliability <= 1.0:
            raise ValueError("Segment reliability must be between 0 and 1")
        self.graph.add_edge(
            segment.start_node_id,
            segment.end_node_id,
            segment_id=segment.id,
            length_m=float(segment.length_m),
            travel_time_s=float(segment.travel_time_s),
            reliability=float(segment.reliability),
            pollution_exposure=float(segment.pollution_exposure),
            source_uri=segment.source_uri,
            scenario_penalty_s=0.0,
            disruption_ids=(),
        )
        self._segments[segment.id] = (segment.start_node_id, segment.end_node_id)

    def remove_segment(self, segment_id: str) -> None:
        endpoints = self._segments.get(segment_id)
        if endpoints is None:
            return
        if self.graph.has_edge(*endpoints):
            self.graph.remove_edge(*endpoints)

    def segment_endpoints(self, segment_id: str) -> tuple[str, str] | None:
        return self._segments.get(segment_id)

    def nearest_node(self, coordinate: Coordinate) -> str:
        if not self.graph.nodes:
            raise ValueError("Cannot search an empty network")
        # Equirectangular approximation is sufficient for snapping over city-scale distances.
        lat0 = math.radians(coordinate.latitude)

        def distance_sq(node_id: str) -> float:
            data = self.graph.nodes[node_id]
            dlat = math.radians(data["latitude"] - coordinate.latitude)
            dlon = math.radians(data["longitude"] - coordinate.longitude) * math.cos(lat0)
            return dlat * dlat + dlon * dlon

        return min(self.graph.nodes, key=distance_sq)

    def segment_ids(self) -> tuple[str, ...]:
        return tuple(self._segments)
