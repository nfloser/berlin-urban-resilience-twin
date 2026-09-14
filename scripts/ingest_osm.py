from __future__ import annotations

import argparse

from urban_resilience_twin.ingestion.osm import OSMDataClient


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download real OSM network/facility data for Berlin"
    )
    parser.add_argument("--place", default="Mitte, Berlin, Germany")
    parser.add_argument("--output", default="data/generated")
    args = parser.parse_args()
    graph_path, facilities_path = OSMDataClient().download_place(args.place, args.output)
    print(f"road network: {graph_path}")
    print(f"facilities: {facilities_path}")


if __name__ == "__main__":
    main()
