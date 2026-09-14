from __future__ import annotations

from rdflib import RDF, Graph, Literal, URIRef
from rdflib.namespace import PROV, XSD

from urban_resilience_twin.domain.models import (
    Disruption,
    District,
    Facility,
    RoadNode,
    RoadSegment,
    Scenario,
)

from .namespaces import URT, WGS84


def _iri(kind: str, identifier: str) -> URIRef:
    return URT[f"{kind}/{identifier}"]


def bind_namespaces(graph: Graph) -> None:
    graph.bind("urt", URT)
    graph.bind("wgs84", WGS84)
    graph.bind("prov", PROV)


def add_district(graph: Graph, district: District) -> URIRef:
    bind_namespaces(graph)
    subject = _iri("district", district.id)
    graph.add((subject, RDF.type, URT.District))
    graph.add((subject, URT.name, Literal(district.name)))
    return subject


def add_road_node(graph: Graph, node: RoadNode) -> URIRef:
    bind_namespaces(graph)
    subject = _iri("road-node", node.id)
    graph.add((subject, RDF.type, URT.RoadNode))
    graph.add((subject, WGS84.lat, Literal(node.coordinate.latitude, datatype=XSD.double)))
    graph.add((subject, WGS84.long, Literal(node.coordinate.longitude, datatype=XSD.double)))
    return subject


def add_road_segment(graph: Graph, segment: RoadSegment) -> URIRef:
    bind_namespaces(graph)
    subject = _iri("road-segment", segment.id)
    graph.add((subject, RDF.type, URT.RoadSegment))
    graph.add((subject, URT.connectsFrom, _iri("road-node", segment.start_node_id)))
    graph.add((subject, URT.connectsTo, _iri("road-node", segment.end_node_id)))
    graph.add((subject, URT.lengthMeters, Literal(segment.length_m, datatype=XSD.double)))
    if segment.source_uri:
        graph.add((subject, PROV.wasDerivedFrom, URIRef(segment.source_uri)))
    return subject


def add_facility(graph: Graph, facility: Facility) -> URIRef:
    bind_namespaces(graph)
    subject = _iri("facility", facility.id)
    graph.add((subject, RDF.type, URT.CriticalFacility))
    graph.add((subject, URT.facilityType, Literal(facility.facility_type.value)))
    graph.add((subject, URT.name, Literal(facility.name)))
    graph.add((subject, URT.locatedIn, _iri("district", facility.district_id)))
    graph.add((subject, URT.connectedTo, _iri("road-node", facility.connected_node_id)))
    graph.add((subject, WGS84.lat, Literal(facility.coordinate.latitude, datatype=XSD.double)))
    graph.add((subject, WGS84.long, Literal(facility.coordinate.longitude, datatype=XSD.double)))
    if facility.source_uri:
        graph.add((subject, PROV.wasDerivedFrom, URIRef(facility.source_uri)))
    return subject


def add_disruption(graph: Graph, disruption: Disruption) -> URIRef:
    bind_namespaces(graph)
    subject = _iri("disruption", disruption.id)
    graph.add((subject, RDF.type, URT.Disruption))
    graph.add((subject, URT.disruptionKind, Literal(disruption.kind.value)))
    graph.add(
        (
            subject,
            URT.startsAt,
            Literal(disruption.starts_at.isoformat(), datatype=XSD.dateTime),
        )
    )
    for segment_id in disruption.affected_segment_ids:
        graph.add((subject, URT.affects, _iri("road-segment", segment_id)))
    for district_id in disruption.affected_district_ids:
        graph.add((subject, URT.affects, _iri("district", district_id)))
    if disruption.source_uri:
        graph.add((subject, PROV.wasDerivedFrom, URIRef(disruption.source_uri)))
    return subject


def add_scenario(graph: Graph, scenario: Scenario) -> URIRef:
    bind_namespaces(graph)
    subject = _iri("scenario", scenario.id)
    graph.add((subject, RDF.type, URT.Scenario))
    graph.add((subject, URT.name, Literal(scenario.name)))
    if scenario.description:
        graph.add((subject, URT.description, Literal(scenario.description)))
    for disruption in scenario.disruptions:
        event = add_disruption(graph, disruption)
        graph.add((subject, URT.includesDisruption, event))
    return subject


def add_analysis_provenance(
    graph: Graph,
    result_id: str,
    source_ids: tuple[str, ...],
    agent_name: str,
) -> URIRef:
    bind_namespaces(graph)
    result = _iri("analysis-result", result_id)
    graph.add((result, RDF.type, URT.AccessibilityResult))
    for source_id in source_ids:
        graph.add((result, PROV.wasDerivedFrom, _iri("source", source_id)))
    agent = _iri("agent", agent_name)
    graph.add((agent, RDF.type, PROV.SoftwareAgent))
    graph.add((result, PROV.wasGeneratedBy, agent))
    return result
