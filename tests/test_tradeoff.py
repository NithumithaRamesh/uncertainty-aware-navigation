"""Tests for route duration and uncertainty trade-off explanations."""

import pytest

from logic.route import Route
from logic.tradeoff import compare_route_tradeoff


def route(
    route_id: str,
    estimated_time: float,
    uncertainty: float,
) -> Route:
    return Route(route_id, f"Route {route_id}", estimated_time, uncertainty, None)


def test_identifies_different_fastest_and_predictable_routes() -> None:
    result = compare_route_tradeoff(
        [route("A", 96, 8), route("B", 100, 3)]
    )

    assert result["fastest_route_id"] == "A"
    assert result["predictable_route_id"] == "B"
    assert result["estimated_time_difference"] == 4
    assert result["uncertainty_difference"] == 5
    assert result["fastest_minimum_time"] == 88
    assert result["fastest_maximum_time"] == 104
    assert result["predictable_minimum_time"] == 97
    assert result["predictable_maximum_time"] == 103
    assert result["same_route"] is False
    assert "approximately 4 minutes faster" in result["explanation"]
    assert "narrower simulated uncertainty range" in result["explanation"]


def test_explains_when_same_route_is_fastest_and_predictable() -> None:
    result = compare_route_tradeoff(
        [route("A", 96, 3), route("B", 100, 8)]
    )

    assert result["fastest_route_id"] == "A"
    assert result["predictable_route_id"] == "A"
    assert result["same_route"] is True
    assert (
        result["explanation"]
        == "Route A has both the lowest estimated journey time and the "
        "lowest simulated uncertainty among the available routes."
    )


def test_supports_a_single_route() -> None:
    result = compare_route_tradeoff([route("A", 96, 3)])

    assert result["fastest_route_id"] == "A"
    assert result["predictable_route_id"] == "A"
    assert result["estimated_time_difference"] == 0
    assert result["uncertainty_difference"] == 0


def test_equal_durations_use_route_id_for_deterministic_ties() -> None:
    result = compare_route_tradeoff(
        [route("B", 96, 3), route("A", 96, 8)]
    )

    assert result["fastest_route_id"] == "A"
    assert result["predictable_route_id"] == "B"
    assert result["estimated_time_difference"] == 0
    assert "same estimated journey time" in result["explanation"]


def test_equal_uncertainty_is_reported_without_claiming_a_difference() -> None:
    result = compare_route_tradeoff(
        [route("A", 96, 3), route("B", 100, 3)]
    )

    assert result["fastest_route_id"] == "A"
    assert result["predictable_route_id"] == "A"
    assert result["uncertainty_difference"] == 0
    assert result["same_route"] is True


def test_equal_duration_and_uncertainty_are_deterministic() -> None:
    result = compare_route_tradeoff(
        [route("B", 96, 3), route("A", 96, 3)]
    )

    assert result["fastest_route_id"] == "A"
    assert result["predictable_route_id"] == "A"
    assert result["same_route"] is True


def test_empty_routes_are_rejected() -> None:
    with pytest.raises(ValueError, match="at least one"):
        compare_route_tradeoff([])


def test_invalid_route_values_are_rejected() -> None:
    with pytest.raises(TypeError, match="only Route"):
        compare_route_tradeoff(["not a route"])  # type: ignore[list-item]
