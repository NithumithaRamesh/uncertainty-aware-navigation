"""Tests for the simulated route data."""

from datetime import datetime, timedelta, timezone

import pytest

from data.sample_routes import get_sample_routes


def test_returns_two_routes_with_expected_simulated_values() -> None:
    current_time = datetime(2026, 11, 16, 12, 0, tzinfo=timezone.utc)

    routes = get_sample_routes(current_time)

    assert [(route.route_id, route.estimated_time, route.uncertainty) for route in routes] == [
        ("A", 35, 2),
        ("B", 27, 10),
    ]
    assert routes[0].last_updated == current_time - timedelta(minutes=5)
    assert routes[1].last_updated == current_time - timedelta(minutes=45)


def test_rejects_naive_reference_time() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        get_sample_routes(datetime(2026, 11, 16, 12, 0))
