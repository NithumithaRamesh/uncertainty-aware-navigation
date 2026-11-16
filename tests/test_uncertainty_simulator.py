"""Tests for deterministic illustrative uncertainty simulation."""

from datetime import datetime, timezone

import pytest

from logic.preference import FASTEST, recommend_by_preference
from logic.recommendation import compare_routes
from logic.route import Route
from logic.route_adapter import routed_routes_to_routes
from services.routing import RoutedRoute
from simulation.uncertainty_simulator import (
    UncertaintySimulationConfig,
    simulate_route_uncertainty,
)


def routes() -> list[Route]:
    return [
        Route("A", "Route A", 30, 0, None),
        Route("B", "Route B", 45, 0, None),
    ]


def test_simulation_is_deterministic_and_non_negative() -> None:
    first = simulate_route_uncertainty(routes())
    second = simulate_route_uncertainty(routes())

    assert first == second
    assert all(0 <= route.uncertainty <= 10 for route in first)


def test_config_controls_the_illustrative_range() -> None:
    simulated = simulate_route_uncertainty(
        routes(),
        UncertaintySimulationConfig(minimum_minutes=4, maximum_minutes=4),
    )

    assert [route.uncertainty for route in simulated] == [4, 4]


def test_simulation_preserves_route_data_and_does_not_mutate_input() -> None:
    original = routes()
    simulated = simulate_route_uncertainty(original)

    assert [route.estimated_time for route in simulated] == [30, 45]
    assert [route.last_updated for route in simulated] == [None, None]
    assert [route.uncertainty for route in original] == [0, 0]


def test_simulation_does_not_depend_on_journey_duration() -> None:
    changed_durations = [
        Route("A", "Route A", 90, 0, None),
        Route("B", "Route B", 15, 0, None),
    ]

    original_values = simulate_route_uncertainty(routes())
    changed_values = simulate_route_uncertainty(changed_durations)

    assert [route.uncertainty for route in original_values] == [
        route.uncertainty for route in changed_values
    ]


def test_empty_routes_are_supported() -> None:
    assert simulate_route_uncertainty([]) == []


def test_invalid_simulation_configuration_is_rejected() -> None:
    with pytest.raises(ValueError):
        UncertaintySimulationConfig(minimum_minutes=11, maximum_minutes=2)


def test_adapter_output_can_be_used_by_recommendation_engines() -> None:
    routed = [
        RoutedRoute("A", 10000, 10, 1800, 30, {}),
        RoutedRoute("B", 12000, 12, 2400, 40, {}),
    ]
    adapted = routed_routes_to_routes(routed)
    simulated = simulate_route_uncertainty(adapted)

    assert all(route.uncertainty >= 0 for route in simulated)
    current_time = datetime.now(timezone.utc)
    comparison = compare_routes(simulated, current_time)
    recommendation = recommend_by_preference(
        simulated, FASTEST, current_time
    )

    assert comparison["fastest_route_id"] == "A"
    assert recommendation["recommended_route_id"] == "A"
