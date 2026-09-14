from __future__ import annotations

from urban_resilience_twin.domain.models import Scenario
from urban_resilience_twin.domain.network import TransportNetwork


class ScenarioEngine:
    """Applies scenario overlays to a copy of the base graph."""

    def derive_network(self, base: TransportNetwork, scenario: Scenario | None) -> TransportNetwork:
        derived = base.copy()
        if scenario is None:
            return derived

        for disruption in scenario.disruptions:
            for segment_id in disruption.affected_segment_ids:
                endpoints = derived.segment_endpoints(segment_id)
                if endpoints is None or not derived.graph.has_edge(*endpoints):
                    continue
                if disruption.closes_segments:
                    derived.graph.remove_edge(*endpoints)
                    continue
                edge = derived.graph.edges[endpoints]
                edge["scenario_penalty_s"] = float(edge.get("scenario_penalty_s", 0.0)) + float(
                    disruption.penalty_seconds
                )
                edge["disruption_ids"] = tuple(edge.get("disruption_ids", ())) + (disruption.id,)
        return derived
