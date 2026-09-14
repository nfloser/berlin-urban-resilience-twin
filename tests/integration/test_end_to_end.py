from fastapi.testclient import TestClient

from urban_resilience_twin.api.app import create_app
from urban_resilience_twin.api.service import build_demo_service


def test_seed_scenario_route_accessibility_workflow() -> None:
    client = TestClient(create_app(build_demo_service()))
    baseline = client.post(
        "/analysis/accessibility",
        json={"origin": {"latitude": 52.52, "longitude": 13.405}, "threshold_minutes": 15},
    ).json()
    assert baseline["reachable_facility_ids"] == ["demo-hospital-c"]

    client.post(
        "/scenario",
        json={
            "id": "isolate",
            "name": "Isolate hospital",
            "disruptions": [
                {"id": "close-bc", "kind": "road_closure", "affected_segment_ids": ["BC"]},
                {"id": "close-dc", "kind": "road_closure", "affected_segment_ids": ["DC"]},
            ],
        },
    )
    disrupted = client.post(
        "/analysis/accessibility",
        json={"origin": {"latitude": 52.52, "longitude": 13.405}, "threshold_minutes": 15},
    ).json()
    assert disrupted["unreachable_facility_ids"] == ["demo-hospital-c"]
