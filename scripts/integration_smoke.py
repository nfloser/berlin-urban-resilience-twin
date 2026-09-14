from __future__ import annotations

import os
import time

import httpx

BASE_URL = os.getenv("API_URL", "http://localhost:8000")


def wait_ready() -> None:
    last_error: Exception | None = None
    for _ in range(60):
        try:
            response = httpx.get(f"{BASE_URL}/ready", timeout=2)
            if response.status_code == 200:
                return
        except Exception as exc:  # noqa: BLE001 - bounded readiness loop
            last_error = exc
        time.sleep(1)
    raise RuntimeError(f"API did not become ready: {last_error}")


def main() -> None:
    wait_ready()
    route_request = {
        "origin": {"latitude": 52.5200, "longitude": 13.4050},
        "destination": {"latitude": 52.5240, "longitude": 13.4150},
        "mode": "fastest",
        "preferences": {},
    }
    baseline = httpx.post(f"{BASE_URL}/route", json=route_request, timeout=10).json()
    assert baseline["segment_ids"] == ["AB", "BC"]

    scenario = {
        "id": "ci-closure",
        "name": "CI closure",
        "disruptions": [
            {"id": "ci-d1", "kind": "road_closure", "affected_segment_ids": ["BC"]}
        ],
    }
    response = httpx.post(f"{BASE_URL}/scenario", json=scenario, timeout=10)
    response.raise_for_status()
    disrupted = httpx.post(f"{BASE_URL}/route", json=route_request, timeout=10).json()
    assert disrupted["segment_ids"] == ["AD", "DC"]
    provenance = httpx.get(f"{BASE_URL}/provenance", timeout=10).json()
    assert provenance["triple_count"] > 0
    print("full-stack integration smoke test passed")


if __name__ == "__main__":
    main()
