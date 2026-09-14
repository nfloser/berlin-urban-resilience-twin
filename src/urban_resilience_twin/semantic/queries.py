from __future__ import annotations

from rdflib import Graph

HOSPITALS_IN_AFFECTED_DISTRICTS = """
PREFIX urt: <https://example.org/berlin-resilience/>
SELECT DISTINCT ?facility WHERE {
  ?event a urt:Disruption ; urt:affects ?district .
  ?district a urt:District .
  ?facility a urt:CriticalFacility ;
            urt:facilityType "hospital" ;
            urt:locatedIn ?district .
}
"""

FACILITIES_CONNECTED_THROUGH_DISRUPTED_SEGMENTS = """
PREFIX urt: <https://example.org/berlin-resilience/>
SELECT DISTINCT ?facility ?segment WHERE {
  ?facility a urt:CriticalFacility ; urt:connectedTo ?node .
  ?segment a urt:RoadSegment .
  { ?segment urt:connectsFrom ?node } UNION { ?segment urt:connectsTo ?node }
  ?event a urt:Disruption ; urt:affects ?segment .
}
"""


def hospitals_in_affected_districts(graph: Graph) -> list[str]:
    return [str(row.facility) for row in graph.query(HOSPITALS_IN_AFFECTED_DISTRICTS)]


def facilities_connected_through_disrupted_segments(graph: Graph) -> list[tuple[str, str]]:
    return [
        (str(row.facility), str(row.segment))
        for row in graph.query(FACILITIES_CONNECTED_THROUGH_DISRUPTED_SEGMENTS)
    ]
