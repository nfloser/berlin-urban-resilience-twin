# Resilience analysis

v1 prioritizes interpretable measurements over composite indices.

Implemented measures include:

- nearest critical-facility travel time,
- number of facilities reachable inside a configurable time threshold,
- facilities that become unreachable,
- change in median facility travel time between baseline and scenario,
- percentage of road segments removed by the active scenario,
- single-segment sensitivity of access to the nearest facility.

Critical-segment analysis removes one candidate segment at a time and recomputes nearest-facility access. On graphs above 500 edges the API requires explicit candidates to prevent an accidental expensive all-edge analysis. This is an operational guard, not a methodological shortcut: callers must state which components are being screened.
