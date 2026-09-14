# Limitations

- Road travel times are free-flow approximations and do not model live congestion.
- Missing OSM `maxspeed` values use documented road-class fallback speeds.
- Parallel OSM edges between the same directed node pair are collapsed to the fastest mapped edge in v1; turn restrictions and lane-level alternatives are not preserved.
- OSM critical-infrastructure coverage can be incomplete or inconsistently tagged.
- v1 routing is road-network based; it is not a complete multimodal VBB journey planner.
- Open-Meteo weather observations are contextual and are not a validated road-closure model.
- Pollution exposure is a routing field/proxy; no scientifically validated Berlin exposure surface is bundled in v1.
- Historical mode is intentionally not exposed because no complete historical network/disruption archive is bundled.
- Facility snapping uses nearest network node and can be wrong around restricted access, campuses or complex entrances.
- Critical-segment analysis is computationally expensive on large graphs and therefore requires explicit candidates above 500 edges.
- Results are research decision support only and are not suitable for emergency dispatch, public-safety navigation or operational incident command.
- No claim is made that the set of facilities is complete or that the resilience metrics capture all social vulnerability dimensions.
