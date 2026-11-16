"""Deterministic illustrative traffic-data freshness for the prototype."""

from collections.abc import Iterable
from dataclasses import replace
from datetime import datetime, timedelta, timezone

from logic.route import Route


SIMULATED_DATA_AGES_MINUTES = {
    "A": 5,
    "B": 45,
    "C": 18,
    "D": 8,
    "E": 35,
}
DEFAULT_DATA_AGE_MINUTES = 15


def simulate_route_freshness(
    routes: Iterable[Route],
    current_time: datetime,
) -> list[Route]:
    """Return routes with deterministic illustrative traffic timestamps.

    OSRM supplies route geometry, distance, and duration, but not traffic-data
    timestamps. These timestamps are simulated for the prototype and are not
    evidence of real traffic-data age.
    """
    if isinstance(routes, (str, bytes)):
        raise TypeError("routes must contain Route objects")
    if not isinstance(current_time, datetime):
        raise TypeError("current_time must be a datetime value")
    if current_time.tzinfo is None or current_time.utcoffset() is None:
        raise ValueError("current_time must be timezone-aware")

    route_list = list(routes)
    if any(not isinstance(route, Route) for route in route_list):
        raise TypeError("routes must contain only Route objects")
    route_ids = [route.route_id for route in route_list]
    if len(route_ids) != len(set(route_ids)):
        raise ValueError("routes must have unique route IDs")

    current_time = current_time.astimezone(timezone.utc)
    return [
        replace(
            route,
            last_updated=current_time
            - timedelta(
                minutes=SIMULATED_DATA_AGES_MINUTES.get(
                    route.route_id,
                    DEFAULT_DATA_AGE_MINUTES,
                )
            ),
        )
        for route in route_list
    ]
