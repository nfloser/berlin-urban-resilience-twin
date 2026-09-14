from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import networkx as nx

from urban_resilience_twin.domain.models import (
    Coordinate,
    Facility,
    FacilityType,
    RoadNode,
    RoadSegment,
)
from urban_resilience_twin.domain.network import TransportNetwork

OSM_ATTRIBUTION = "© OpenStreetMap contributors"


def _speed_kmh(value: Any, highway: Any = None) -> float:
    if isinstance(value, list):
        value = value[0] if value else None
    if value is not None:
        text = str(value).lower().replace("km/h", "").strip()
        if "mph" in text:
            try:
                return float(text.replace("mph", "").strip()) * 1.60934
            except ValueError:
                pass
        try:
            return float(text)
        except ValueError:
            pass
    if isinstance(highway, list):
        highway = highway[0] if highway else None
    defaults = {"motorway": 80.0, "trunk": 70.0, "primary": 50.0, "secondary": 50.0}
    return defaults.get(str(highway), 30.0)


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


class OSMNetworkMapper:
    def map_graph(self, graph: nx.MultiDiGraph) -> TransportNetwork:
        network = TransportNetwork()
        for node_id, data in graph.nodes(data=True):
            network.add_node(
                RoadNode(
                    id=str(node_id),
                    coordinate=Coordinate(latitude=float(data["y"]), longitude=float(data["x"])),
                )
            )
        seen_pairs: dict[tuple[str, str], tuple[float, RoadSegment]] = {}
        for u, v, key, data in graph.edges(keys=True, data=True):
            length_m = float(data.get("length", 0.0))
            speed_kmh = _speed_kmh(data.get("maxspeed"), data.get("highway"))
            travel_time_s = 0.0 if speed_kmh <= 0 else length_m / (speed_kmh / 3.6)
            osmid = data.get("osmid")
            if isinstance(osmid, list):
                osmid = osmid[0] if osmid else None
            sid = f"osm-way-{osmid or f'{u}-{v}-{key}'}:{u}:{v}:{key}"
            segment = RoadSegment(
                id=sid,
                start_node_id=str(u),
                end_node_id=str(v),
                length_m=length_m,
                travel_time_s=travel_time_s,
                source_uri=f"https://www.openstreetmap.org/way/{osmid}" if osmid else None,
            )
            pair = (str(u), str(v))
            current = seen_pairs.get(pair)
            if current is None or travel_time_s < current[0]:
                seen_pairs[pair] = (travel_time_s, segment)
        for _, segment in seen_pairs.values():
            network.add_segment(segment)
        return network


def write_network_json(network: TransportNetwork, path: str | Path) -> Path:
    path = Path(path)
    payload = {
        "nodes": [
            {
                "id": str(node_id),
                "latitude": float(data["latitude"]),
                "longitude": float(data["longitude"]),
            }
            for node_id, data in network.graph.nodes(data=True)
        ],
        "segments": [
            {
                "id": str(data["segment_id"]),
                "start_node_id": str(u),
                "end_node_id": str(v),
                "length_m": float(data["length_m"]),
                "travel_time_s": float(data["travel_time_s"]),
                "reliability": float(data.get("reliability", 1.0)),
                "pollution_exposure": float(data.get("pollution_exposure", 0.0)),
                "source_uri": data.get("source_uri"),
            }
            for u, v, data in network.graph.edges(data=True)
        ],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def load_network_json(path: str | Path) -> TransportNetwork:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    network = TransportNetwork()
    for item in payload["nodes"]:
        network.add_node(
            RoadNode(
                str(item["id"]),
                Coordinate(float(item["latitude"]), float(item["longitude"])),
            )
        )
    for item in payload["segments"]:
        network.add_segment(
            RoadSegment(
                id=str(item["id"]),
                start_node_id=str(item["start_node_id"]),
                end_node_id=str(item["end_node_id"]),
                length_m=float(item["length_m"]),
                travel_time_s=float(item["travel_time_s"]),
                reliability=float(item.get("reliability", 1.0)),
                pollution_exposure=float(item.get("pollution_exposure", 0.0)),
                source_uri=item.get("source_uri"),
            )
        )
    return network


def load_facilities_json(path: str | Path) -> list[Facility]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return [
        Facility(
            id=str(item["id"]),
            name=str(item["name"]),
            facility_type=FacilityType(str(item["facility_type"])),
            coordinate=Coordinate(float(item["latitude"]), float(item["longitude"])),
            district_id=str(item["district_id"]),
            connected_node_id=str(item["connected_node_id"]),
            source_uri=item.get("source_uri"),
        )
        for item in payload
    ]


class OSMDataClient:
    """Downloads real road and critical-facility data from OpenStreetMap via OSMnx."""

    def download_place(self, place: str, output_dir: str | Path) -> tuple[Path, Path]:
        try:
            import osmnx as ox
        except ImportError as exc:
            raise RuntimeError("Install the 'ingestion' extra to download OSM data") from exc

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        graph = ox.graph.graph_from_place(place, network_type="drive", simplify=True)
        raw_graph_path = output_dir / "road-network.graphml"
        ox.io.save_graphml(graph, raw_graph_path)
        network = OSMNetworkMapper().map_graph(graph)
        network_path = write_network_json(network, output_dir / "network.json")

        facilities_gdf = ox.features.features_from_place(
            place,
            tags={"amenity": ["hospital", "fire_station"]},
        )
        facilities_gdf.to_file(output_dir / "facilities.geojson", driver="GeoJSON")
        district_name = place.split(",", maxsplit=1)[0].strip()
        district_id = _slug(district_name)
        normalized: list[dict[str, Any]] = []
        for index, row in facilities_gdf.iterrows():
            amenity = row.get("amenity")
            if amenity not in {"hospital", "fire_station"} or row.geometry is None:
                continue
            point = row.geometry if row.geometry.geom_type == "Point" else row.geometry.centroid
            coordinate = Coordinate(latitude=float(point.y), longitude=float(point.x))
            connected_node = network.nearest_node(coordinate)
            if isinstance(index, tuple) and len(index) == 2:
                osm_type, osm_id = str(index[0]), str(index[1])
            else:
                osm_type, osm_id = "element", str(index)
            facility_type = "hospital" if amenity == "hospital" else "fire_station"
            normalized.append(
                {
                    "id": f"osm-{osm_type}-{osm_id}",
                    "name": str(row.get("name") or f"Unnamed {facility_type}"),
                    "facility_type": facility_type,
                    "latitude": coordinate.latitude,
                    "longitude": coordinate.longitude,
                    "district_id": district_id,
                    "connected_node_id": connected_node,
                    "source_uri": f"https://www.openstreetmap.org/{osm_type}/{osm_id}",
                }
            )
        facilities_path = output_dir / "facilities.json"
        facilities_path.write_text(json.dumps(normalized, indent=2), encoding="utf-8")
        metadata = {
            "source": "OpenStreetMap",
            "attribution": OSM_ATTRIBUTION,
            "place_query": place,
            "district_id": district_id,
            "raw_graph": raw_graph_path.name,
            "raw_facilities": "facilities.geojson",
        }
        (output_dir / "source-metadata.json").write_text(
            json.dumps(metadata, indent=2), encoding="utf-8"
        )
        return network_path, facilities_path
