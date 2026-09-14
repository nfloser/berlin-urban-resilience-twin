# ADR-001: Separate network computation from semantic persistence

**Status:** Accepted

NetworkX is used for topology algorithms; RDF/Fuseki is used for semantic relationships and provenance. Large road topology is normalized outside RDF for runtime computation. This prevents RDF from becoming an inefficient substitute for a routing graph while retaining queryable cross-domain meaning.
