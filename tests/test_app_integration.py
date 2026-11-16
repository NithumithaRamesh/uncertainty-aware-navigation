"""Focused tests for the dynamic application route pipeline."""

from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from app import _retrieve_route_data
from services.geocoding import GeocodedPlace
from services.routing import (
    RoutedRoute,
    RoutingConnectionError,
)


ORIGIN = GeocodedPlace("Birmingham", "Birmingham, UK", 52.48, -1.9, "relation", 1)
DESTINATION = GeocodedPlace(
    "Manchester", "Manchester, UK", 53.48, -2.24, "relation", 2
)
GEOMETRY = {
    "type": "LineString",
    "coordinates": [[-1.9, 52.48], [-2.24, 53.48]],
}


def routed_route(route_id: str, duration_minutes: float) -> RoutedRoute:
    return RoutedRoute(
        route_id=route_id,
        distance_metres=10000,
        distance_km=10,
        duration_seconds=duration_minutes * 60,
        duration_minutes=duration_minutes,
        geometry=GEOMETRY,
    )


def test_dynamic_pipeline_converts_multiple_external_routes() -> None:
    external_routes = [routed_route("A", 30), routed_route("B", 40)]
    current_time = datetime(2026, 11, 16, 12, 0, tzinfo=timezone.utc)
    with patch("app.get_routes", return_value=external_routes) as get_routes:
        routed, routes = _retrieve_route_data(
            ORIGIN,
            DESTINATION,
            current_time,
        )

    get_routes.assert_called_once_with(ORIGIN, DESTINATION)
    assert routed == external_routes
    assert [route.route_id for route in routes] == ["A", "B"]
    assert [route.estimated_time for route in routes] == [30, 40]
    assert all(route.uncertainty >= 0 for route in routes)
    assert [
        (current_time - route.last_updated).total_seconds() / 60
        for route in routes
        if route.last_updated is not None
    ] == [5, 45]


def test_dynamic_pipeline_preserves_a_single_available_route() -> None:
    with patch(
        "app.get_routes",
        return_value=[routed_route("A", 30)],
    ):
        _, routes = _retrieve_route_data(ORIGIN, DESTINATION)

    assert [route.route_id for route in routes] == ["A"]


def test_dynamic_pipeline_surfaces_routing_failures() -> None:
    with patch(
        "app.get_routes",
        side_effect=RoutingConnectionError("offline"),
    ):
        with pytest.raises(RoutingConnectionError, match="offline"):
            _retrieve_route_data(ORIGIN, DESTINATION)
