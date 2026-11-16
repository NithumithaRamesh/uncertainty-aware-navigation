from datetime import datetime, timezone

import pytest

from logic.route import Route
from simulation.freshness_simulator import simulate_route_freshness


CURRENT_TIME = datetime(2026, 11, 16, 12, 0, tzinfo=timezone.utc)


def test_simulates_distinct_deterministic_route_ages() -> None:
    routes = [
        Route("A", "Route A", 30, 2, None),
        Route("B", "Route B", 40, 3, None),
    ]

    first = simulate_route_freshness(routes, CURRENT_TIME)
    second = simulate_route_freshness(routes, CURRENT_TIME)

    assert first == second
    assert [
        (CURRENT_TIME - route.last_updated).total_seconds() / 60
        for route in first
        if route.last_updated is not None
    ] == [5, 45]


def test_simulation_preserves_route_estimates_and_does_not_mutate_input() -> None:
    original = [Route("A", "Route A", 30, 2, None)]

    simulated = simulate_route_freshness(original, CURRENT_TIME)

    assert simulated[0].estimated_time == 30
    assert simulated[0].uncertainty == 2
    assert original[0].last_updated is None


def test_requires_timezone_aware_current_time() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        simulate_route_freshness(
            [Route("A", "Route A", 30, 2, None)],
            datetime(2026, 11, 16, 12, 0),
        )
