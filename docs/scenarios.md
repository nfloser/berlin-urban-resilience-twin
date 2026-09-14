# Scenario system

A scenario is an explicit overlay containing one or more disruptions. The base network is never permanently modified.

```text
Base network + Scenario overlay -> Derived network -> Route/accessibility result
```

Current effects:

- `road_closure`: remove affected segment from the derived network,
- `road_penalty`: retain segment but add a stated penalty,
- `severe_weather`: semantic event that can affect districts or segments,
- `high_pollution`: semantic/environmental disruption type available for scenario modelling.

A weather observation is not converted automatically into road closures. Such a conversion would require an evidence-backed hazard-impact model that is outside the v1 scope.
