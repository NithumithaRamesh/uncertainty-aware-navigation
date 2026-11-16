"""Tests for travel-time uncertainty calculations."""

from datetime import datetime

from logic.route import Route
from logic.uncertainty import calculate_time_range


def make_route(estimated_time: float, uncertainty: float) -> Route:
    return Route(
        route_id="A",
        name="M6",
        estimated_time=estimated_time,
        uncertainty=uncertainty,
        last_updated=datetime(2026, 11, 15, 10, 55),
    )


def test_calculates_route_a_range() -> None:
    assert calculate_time_range(make_route(35, 2)) == (33, 37)


def test_calculates_route_b_range() -> None:
    assert calculate_time_range(make_route(27, 10)) == (17, 37)


def test_zero_uncertainty_has_equal_bounds() -> None:
    assert calculate_time_range(make_route(35, 0)) == (35, 35)
