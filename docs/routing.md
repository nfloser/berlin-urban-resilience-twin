# Routing

## Fastest

Dijkstra minimizes `travel_time_s`. Closed segments are removed by the scenario overlay and therefore cannot be used.

## Disruption avoiding

```text
cost = travel_time + disruption_weight * scenario_penalty
```

## Most reliable

```text
reliability_penalty = travel_time * (1 - segment_reliability)
cost = travel_time
     + reliability_weight * reliability_penalty
     + disruption_weight * scenario_penalty
```

## Lowest exposure

```text
cost = travel_time
     + pollution_weight * exposure_proxy
     + disruption_weight * scenario_penalty
```

The weights are user or scenario preferences. They are not scientific constants and are never described as a validated resilience score. The API returns the route's physical travel time separately from its generalized optimization cost.

## Explainability

Every route response includes path nodes, segment IDs, geometry, travel time, distance, affected segments, exposure proxy, mean reliability, generalized cost and a plain-language rationale.
