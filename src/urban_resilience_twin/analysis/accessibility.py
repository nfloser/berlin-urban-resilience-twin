from __future__ import annotations

import statistics

import networkx as nx

from urban_resilience_twin.domain.models import (
    AccessibilityMetrics,
    Facility,
    Scenario,
    ScenarioComparison,
)
from urban_resilience_twin.domain.network import TransportNetwork
from urban_resilience_twin.scenarios.engine import ScenarioEngine


class AccessibilityAnalyzer:
    def __init__(self, scenario_engine: ScenarioEngine | None = None) -> None:
        self.scenario_engine = scenario_engine or ScenarioEngine()

    def measure(
        self,
        network: TransportNetwork,
        origin_node_id: str,
        facilities: list[Facility],
        threshold_s: float = 900.0,
        scenario: Scenario | None = None,
    ) -> AccessibilityMetrics:
        derived = self.scenario_engine.derive_network(network, scenario)
        lengths = nx.single_source_dijkstra_path_length(
            derived.graph, origin_node_id, weight="travel_time_s"
        )
        times: dict[str, float] = {}
        unreachable: list[str] = []
        for facility in facilities:
            value = lengths.get(facility.connected_node_id)
            if value is None:
                unreachable.append(facility.id)
            else:
                times[facility.id] = float(value)

        reachable = tuple(sorted(fid for fid, value in times.items() if value <= threshold_s))
        nearest_id = min(times, key=times.get) if times else None
        nearest_time = times[nearest_id] if nearest_id else None
        median = statistics.median(times.values()) if times else None
        return AccessibilityMetrics(
            origin_node_id=origin_node_id,
            threshold_s=threshold_s,
            reachable_facility_ids=reachable,
            unreachable_facility_ids=tuple(sorted(unreachable)),
            nearest_facility_id=nearest_id,
            nearest_facility_travel_time_s=nearest_time,
            median_facility_travel_time_s=median,
        )

    def compare(
        self,
        network: TransportNetwork,
        origin_node_id: str,
        facilities: list[Facility],
        threshold_s: float,
        scenario: Scenario,
    ) -> ScenarioComparison:
        baseline = self.measure(network, origin_node_id, facilities, threshold_s, scenario=None)
        disrupted = self.measure(
            network, origin_node_id, facilities, threshold_s, scenario=scenario
        )
        if (
            baseline.median_facility_travel_time_s is None
            or disrupted.median_facility_travel_time_s is None
        ):
            delta = None
        else:
            delta = disrupted.median_facility_travel_time_s - baseline.median_facility_travel_time_s
        became_unreachable = tuple(
            sorted(
                set(disrupted.unreachable_facility_ids)
                - set(baseline.unreachable_facility_ids)
            )
        )
        return ScenarioComparison(
            baseline=baseline,
            disrupted=disrupted,
            reachable_facility_change=(
                len(disrupted.reachable_facility_ids) - len(baseline.reachable_facility_ids)
            ),
            median_travel_time_change_s=delta,
            facilities_becoming_unreachable=became_unreachable,
        )
