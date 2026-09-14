from __future__ import annotations

import statistics

import networkx as nx

from urban_resilience_twin.domain.models import RouteMode, RoutePreferences, RouteResult, Scenario
from urban_resilience_twin.domain.network import TransportNetwork
from urban_resilience_twin.scenarios.engine import ScenarioEngine


class RouteNotFoundError(RuntimeError):
    pass


class Router:
    def __init__(self, scenario_engine: ScenarioEngine | None = None) -> None:
        self.scenario_engine = scenario_engine or ScenarioEngine()

    @staticmethod
    def _edge_cost(mode: RouteMode, preferences: RoutePreferences):
        def cost(_u: str, _v: str, data: dict) -> float:
            travel = float(data["travel_time_s"])
            scenario_penalty = float(data.get("scenario_penalty_s", 0.0))
            reliability = float(data.get("reliability", 1.0))
            exposure = float(data.get("pollution_exposure", 0.0))
            if mode == RouteMode.FASTEST:
                return travel
            if mode == RouteMode.DISRUPTION_AVOIDING:
                return travel + preferences.disruption_weight * scenario_penalty
            if mode == RouteMode.MOST_RELIABLE:
                reliability_penalty = travel * (1.0 - reliability)
                return (
                    travel
                    + preferences.reliability_weight * reliability_penalty
                    + preferences.disruption_weight * scenario_penalty
                )
            if mode == RouteMode.LOWEST_EXPOSURE:
                return (
                    travel
                    + preferences.pollution_weight * exposure
                    + preferences.disruption_weight * scenario_penalty
                )
            raise ValueError(f"Unsupported route mode: {mode}")

        return cost

    def route(
        self,
        network: TransportNetwork,
        origin_node_id: str,
        destination_node_id: str,
        mode: RouteMode = RouteMode.FASTEST,
        preferences: RoutePreferences | None = None,
        scenario: Scenario | None = None,
    ) -> RouteResult:
        preferences = preferences or RoutePreferences()
        derived = self.scenario_engine.derive_network(network, scenario)
        try:
            path = nx.shortest_path(
                derived.graph,
                origin_node_id,
                destination_node_id,
                weight=self._edge_cost(mode, preferences),
                method="dijkstra",
            )
        except (nx.NetworkXNoPath, nx.NodeNotFound) as exc:
            raise RouteNotFoundError(str(exc)) from exc

        distance = 0.0
        travel_time = 0.0
        generalized_cost = 0.0
        exposure = 0.0
        reliabilities: list[float] = []
        affected: list[str] = []
        segments: list[str] = []
        cost_fn = self._edge_cost(mode, preferences)
        for u, v in zip(path, path[1:], strict=False):
            data = derived.graph.edges[u, v]
            segments.append(str(data["segment_id"]))
            distance += float(data["length_m"])
            travel_time += float(data["travel_time_s"])
            exposure += float(data.get("pollution_exposure", 0.0))
            reliabilities.append(float(data.get("reliability", 1.0)))
            generalized_cost += cost_fn(u, v, data)
            if data.get("disruption_ids"):
                affected.append(str(data["segment_id"]))

        mean_reliability = statistics.fmean(reliabilities) if reliabilities else 1.0
        explanation = self._explain(mode, travel_time, affected, exposure, mean_reliability)
        return RouteResult(
            path_node_ids=tuple(path),
            segment_ids=tuple(segments),
            distance_m=distance,
            travel_time_s=travel_time,
            generalized_cost=generalized_cost,
            affected_segment_ids=tuple(affected),
            pollution_exposure=exposure,
            mean_reliability=mean_reliability,
            explanation=explanation,
        )

    @staticmethod
    def _explain(
        mode: RouteMode,
        travel_time_s: float,
        affected_segments: list[str],
        exposure: float,
        reliability: float,
    ) -> str:
        minutes = travel_time_s / 60.0
        if mode == RouteMode.FASTEST:
            return f"Fastest available route; estimated free-flow travel time is {minutes:.1f} min."
        if mode == RouteMode.DISRUPTION_AVOIDING:
            return (
                "Disruption-aware route; "
                f"{len(affected_segments)} penalised segment(s) remain on the path."
            )
        if mode == RouteMode.MOST_RELIABLE:
            return f"Reliability-weighted route; mean segment reliability is {reliability:.2f}."
        return f"Exposure-weighted route; cumulative exposure proxy is {exposure:.1f}."
