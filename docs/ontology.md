# Semantic model

The project reuses WGS84 coordinates and PROV-O provenance and introduces a deliberately small project namespace (`urt:`) for resilience-specific relationships.

Core relationships:

```text
CriticalFacility --locatedIn--> District
CriticalFacility --connectedTo--> RoadNode
RoadSegment --connectsFrom--> RoadNode
RoadSegment --connectsTo--> RoadNode
Disruption --affects--> RoadSegment | District
Scenario --includesDisruption--> Disruption
AnalysisResult --prov:wasDerivedFrom--> source/scenario
AnalysisResult --prov:wasGeneratedBy--> SoftwareAgent
```

The knowledge graph is used by tested SPARQL queries, not only for storage. For example, `HOSPITALS_IN_AFFECTED_DISTRICTS` traverses disruption → district → hospital, while `FACILITIES_CONNECTED_THROUGH_DISRUPTED_SEGMENTS` traverses facility → connected road node ← road segment ← disruption.

## SHACL contracts

Before publication to Fuseki:

- road segments require exactly one start and end node and a numeric length,
- critical facilities require network connection, administrative area and coordinates,
- disruptions require kind, timestamp and at least one affected entity.

The runtime refuses to publish a graph that fails these constraints.
