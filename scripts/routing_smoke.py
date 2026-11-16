"""Manual Birmingham-to-Manchester geocoding and OSRM routing smoke test."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.geocoding import search_cities
from services.routing import get_routes


def main() -> None:
    origin_results = search_cities("Birmingham")
    destination_results = search_cities("Manchester")
    if not origin_results or not destination_results:
        raise RuntimeError("Could not geocode Birmingham or Manchester")

    routes = get_routes(origin_results[0], destination_results[0])
    for route in routes:
        print(
            f"Route {route.route_id}: {route.distance_km:.1f} km, "
            f"{route.duration_minutes:.1f} minutes, "
            f"{len(route.geometry['coordinates'])} geometry points"
        )


if __name__ == "__main__":
    main()
