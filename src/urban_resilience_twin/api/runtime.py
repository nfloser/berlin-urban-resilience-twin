from __future__ import annotations

import json
import os
from pathlib import Path

from urban_resilience_twin.domain.models import District
from urban_resilience_twin.ingestion.osm import load_facilities_json, load_network_json

from .service import TwinService, build_demo_service


def load_service_from_environment() -> TwinService:
    network_path = os.getenv("URT_NETWORK_JSON")
    facilities_path = os.getenv("URT_FACILITIES_JSON")
    if not network_path or not facilities_path:
        return build_demo_service()
    if not Path(network_path).exists() or not Path(facilities_path).exists():
        raise RuntimeError("Configured OSM snapshot paths do not exist")
    network = load_network_json(network_path)
    facilities = load_facilities_json(facilities_path)
    district_id = os.getenv("URT_DISTRICT_ID", "mitte")
    district_name = os.getenv("URT_DISTRICT_NAME", "Mitte")
    metadata_path = os.getenv("URT_SOURCE_METADATA")
    if metadata_path and Path(metadata_path).exists():
        metadata = json.loads(Path(metadata_path).read_text(encoding="utf-8"))
        district_id = str(metadata.get("district_id", district_id))
        district_name = str(metadata.get("place_query", district_name)).split(",", 1)[0]
    return TwinService(
        network,
        facilities,
        [District(district_id, district_name)],
        data_mode="osm-snapshot",
    )
