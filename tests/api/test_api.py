from fastapi.testclient import TestClient

from urban_resilience_twin.api.app import create_app
from urban_resilience_twin.api.service import build_demo_service


def client() -> TestClient:
    return TestClient(create_app(build_demo_service()))


def test_health_and_route_endpoint() -> None:
    api = client()
    assert api.get("/health").status_code == 200
    response = api.post(
        "/route",
        json={
            "origin": {"latitude": 52.5200, "longitude": 13.4050},
            "destination": {"latitude": 52.5240, "longitude": 13.4150},
            "mode": "fastest",
            "preferences": {},
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["segment_ids"] == ["AB", "BC"]
    assert body["explanation"]


def test_scenario_changes_route_and_provenance_is_exposed() -> None:
    api = client()
    scenario = {
        "id": "closure",
        "name": "Close BC",
        "disruptions": [
            {"id": "d1", "kind": "road_closure", "affected_segment_ids": ["BC"]}
        ],
    }
    assert api.post("/scenario", json=scenario).status_code == 200
    response = api.post(
        "/route",
        json={
            "origin": {"latitude": 52.5200, "longitude": 13.4050},
            "destination": {"latitude": 52.5240, "longitude": 13.4150},
            "mode": "fastest",
            "preferences": {},
        },
    )
    assert response.json()["segment_ids"] == ["AD", "DC"]
    provenance = api.get("/provenance").json()
    assert provenance["triple_count"] > 0


def test_network_segments_expose_active_disruption_state() -> None:
    api = client()
    baseline = api.get("/network/segments")
    assert baseline.status_code == 200
    bc = next(
        feature
        for feature in baseline.json()["features"]
        if feature["properties"]["segment_id"] == "BC"
    )
    assert bc["properties"]["affected"] is False

    scenario = {
        "id": "closure",
        "name": "Close BC",
        "disruptions": [
            {"id": "d1", "kind": "road_closure", "affected_segment_ids": ["BC"]}
        ],
    }
    api.post("/scenario", json=scenario).raise_for_status()
    disrupted = api.get("/network/segments").json()
    bc = next(
        feature
        for feature in disrupted["features"]
        if feature["properties"]["segment_id"] == "BC"
    )
    assert bc["properties"]["affected"] is True


def test_semantic_impact_uses_linked_graph_relationships() -> None:
    api = client()
    scenario = {
        "id": "semantic-closure",
        "name": "Semantic closure",
        "disruptions": [
            {"id": "d-sem", "kind": "road_closure", "affected_segment_ids": ["BC"]}
        ],
    }
    api.post("/scenario", json=scenario).raise_for_status()
    impact = api.get("/analysis/semantic-impact")
    assert impact.status_code == 200
    linked = impact.json()["facilities_connected_through_disrupted_segments"]
    assert any("demo-hospital-c" in item["facility"] for item in linked)
