"""Transparent route comparison and recommendation logic."""

from datetime import datetime
from typing import TypedDict

from .freshness import assess_freshness
from .route import Route
from .uncertainty import calculate_time_range


class RouteComparison(TypedDict):
    """Values required to display one route's comparison details."""

    route_id: str
    estimated_time: float
    minimum_time: float
    maximum_time: float
    data_age_minutes: float | None
    freshness: str


class ComparisonResult(TypedDict):
    """Structured output for a route comparison."""

    fastest_route_id: str
    explanation: str
    routes: list[RouteComparison]


def compare_routes(
    routes: list[Route],
    current_time: datetime,
) -> ComparisonResult:
    """Compare routes by estimated time and describe their trade-offs.

    The fastest route is selected using only ``estimated_time``. Uncertainty
    and freshness are reported separately so the user can make the final
    decision without an arbitrary combined score.

    Raises:
        ValueError: If ``routes`` is empty.
        TypeError: If ``current_time`` is not a datetime or a route is not a
            ``Route`` instance.
    """
    if not routes:
        raise ValueError("routes must contain at least one route")
    if not isinstance(current_time, datetime):
        raise TypeError("current_time must be a datetime value")
    if any(not isinstance(route, Route) for route in routes):
        raise TypeError("routes must contain only Route instances")

    fastest_route = min(routes, key=lambda route: route.estimated_time)
    route_details: list[RouteComparison] = []

    for route in routes:
        minimum_time, maximum_time = calculate_time_range(route)
        if route.last_updated is None:
            data_age_minutes, freshness = None, "Unavailable"
        else:
            data_age_minutes, freshness = assess_freshness(
                route.last_updated, current_time
            )

        route_details.append(
            {
                "route_id": route.route_id,
                "estimated_time": route.estimated_time,
                "minimum_time": minimum_time,
                "maximum_time": maximum_time,
                "data_age_minutes": data_age_minutes,
                "freshness": freshness,
            }
        )

    fastest_details = next(
        detail
        for detail in route_details
        if detail["route_id"] == fastest_route.route_id
    )
    explanation = (
        f"Route {fastest_route.route_id} has the lowest estimated journey time "
        f"at {fastest_route.estimated_time:g} minutes. Its estimated range is "
        f"{fastest_details['minimum_time']:g}–"
        f"{fastest_details['maximum_time']:g} minutes. Traffic information "
        f"is {fastest_details['freshness'].lower()}."
    )

    return {
        "fastest_route_id": fastest_route.route_id,
        "explanation": explanation,
        "routes": route_details,
    }
