# Semantic model

The project reuses WGS84 coordinates and PROV-O provenance and introduces a deliberately small project namespace (`urt:`) for resilience-specific relationships.

Core relationships:

```text
CriticalFacility --locatedIn--> District
CriticalFacility --connectedTo--> RoadNode
RoadSegment --connectsFrom--> RoadNode
RoadSegment --connectsTo--> RoadNode
Disruption --affects--> RoadSegment | District
RouteResult --originNode/destinationNode--> RoadNode
RouteResult --routeMode--> routing objective
AnalysisResult --prov:wasDerivedFrom--> source/scenario
AnalysisResult --prov:wasGeneratedBy--> SoftwareAgent
```

The knowledge graph is used by tested SPARQL queries, not only for storage. For example, `HOSPITALS_IN_AFFECTED_DISTRICTS` traverses disruption → district → hospital, while `FACILITIES_CONNECTED_THROUGH_DISRUPTED_SEGMENTS` traverses facility → connected road node ← road segment ← disruption.

## SHACL contracts

Before publication to Fuseki:

- road segments require exactly one start and end node and a numeric length,
- critical facilities require network connection, administrative area and coordinates,
- disruptions require kind, timestamp and at least one affected entity,
- route results require origin, destination, routing mode, source provenance and generating agent,
- accessibility results require source provenance and generating agent.

The runtime refuses to publish a graph that fails these constraints.

The API endpoint `GET /analysis/semantic-impact` executes the linked-domain SPARQL queries against the active semantic graph, so the knowledge graph participates directly in decision-support behaviour rather than acting as a decorative datastore.
