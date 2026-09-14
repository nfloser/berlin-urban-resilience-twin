from __future__ import annotations

from pathlib import Path

from rdflib import Graph


def validate_graph(data_graph: Graph, shapes_path: str | Path) -> tuple[bool, str]:
    try:
        from pyshacl import validate
    except ImportError as exc:  # pragma: no cover - dependency is mandatory in packaged runtime
        raise RuntimeError("pyshacl is required for semantic validation") from exc

    conforms, _, text = validate(
        data_graph=data_graph,
        shacl_graph=str(shapes_path),
        inference="rdfs",
        abort_on_first=False,
        allow_infos=False,
        allow_warnings=False,
    )
    return bool(conforms), str(text)
