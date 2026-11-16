"""Tests for the simulated route data."""

from datetime import datetime, timedelta, timezone

import pytest

from data.sample_routes import get_sample_routes


def test_returns_five_routes_with_expected_simulated_values() -> None:
    current_time = datetime(2026, 11, 16, 12, 0, tzinfo=timezone.utc)

    routes = get_sample_routes(current_time)

    assert [
        (route.route_id, route.name, route.estimated_time, route.uncertainty)
        for route in routes
    ] == [
        ("A", "Route A", 27, 10),
        ("B", "Route B", 35, 2),
        ("C", "Route C", 32, 3),
        ("D", "Route D", 29, 5),
        ("E", "Route E", 38, 4),
    ]
    assert [
        current_time - route.last_updated for route in routes
    ] == [
        timedelta(minutes=45),
        timedelta(minutes=5),
        timedelta(minutes=8),
        timedelta(minutes=18),
        timedelta(minutes=22),
    ]
    assert all(
        route.last_updated is not None
        and route.last_updated.tzinfo == timezone.utc
        for route in routes
    )


def test_rejects_naive_reference_time() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        get_sample_routes(datetime(2026, 11, 16, 12, 0))
