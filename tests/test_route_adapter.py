"""Tests for converting routed service results into application routes."""

import pytest

from logic.route_adapter import routed_routes_to_routes
from services.routing import RoutedRoute


def routed_route(
    route_id: str = "A",
    duration_minutes: float = 30,
) -> RoutedRoute:
    return RoutedRoute(
        route_id=route_id,
        distance_metres=10000,
        distance_km=10,
        duration_seconds=duration_minutes * 60,
        duration_minutes=duration_minutes,
        geometry={
            "type": "LineString",
            "coordinates": [[-1.9, 52.48], [-2.24, 53.48]],
        },
    )


def test_converts_multiple_routes_and_preserves_identity_and_duration() -> None:
    routes = routed_routes_to_routes(
        [routed_route("A", 30), routed_route("B", 42.5)]
    )

    assert [(route.route_id, route.name, route.estimated_time) for route in routes] == [
        ("A", "Route A", 30),
        ("B", "Route B", 42.5),
    ]


def test_external_routes_have_no_fabricated_traffic_timestamp() -> None:
    route = routed_routes_to_routes([routed_route()])[0]

    assert route.last_updated is None
    assert route.uncertainty == 0


def test_empty_route_collection_is_supported() -> None:
    assert routed_routes_to_routes([]) == []


@pytest.mark.parametrize(
    "invalid_route",
    [
        "not a route",
        routed_route("A", 0),
        routed_route("A", float("nan")),
    ],
)
def test_invalid_route_data_is_rejected(invalid_route: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        routed_routes_to_routes([invalid_route])  # type: ignore[list-item]


def test_duplicate_route_ids_are_rejected() -> None:
    with pytest.raises(ValueError, match="unique"):
        routed_routes_to_routes([routed_route("A"), routed_route("A", 31)])
