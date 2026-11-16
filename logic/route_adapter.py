"""Adapters between external routing results and the application route model."""

import math
from collections.abc import Iterable

from services.routing import RoutedRoute

from .route import Route


def routed_routes_to_routes(
    routed_routes: Iterable[RoutedRoute],
) -> list[Route]:
    """Convert OSRM routes into application routes.

    OSRM does not provide traffic-data timestamps or calibrated uncertainty.
    Those fields are therefore left at neutral values for a separate
    simulation step: ``uncertainty=0`` and ``last_updated=None``.
    """
    if isinstance(routed_routes, (str, bytes)):
        raise TypeError("routed_routes must contain RoutedRoute objects")

    routes = list(routed_routes)
    converted: list[Route] = []
    seen_ids: set[str] = set()
    for routed_route in routes:
        if not isinstance(routed_route, RoutedRoute):
            raise TypeError("routed_routes must contain RoutedRoute objects")
        if (
            not isinstance(routed_route.duration_minutes, (int, float))
            or isinstance(routed_route.duration_minutes, bool)
            or not math.isfinite(routed_route.duration_minutes)
            or routed_route.duration_minutes <= 0
        ):
            raise ValueError(
                "routed route duration_minutes must be a positive finite number"
            )
        if routed_route.route_id in seen_ids:
            raise ValueError("routed routes must have unique route IDs")
        seen_ids.add(routed_route.route_id)
        converted.append(
            Route(
                route_id=routed_route.route_id,
                name=f"Route {routed_route.route_id}",
                estimated_time=routed_route.duration_minutes,
                uncertainty=0.0,
                last_updated=None,
            )
        )
    return converted
