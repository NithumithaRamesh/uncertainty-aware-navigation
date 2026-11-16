"""Tests for route comparison and recommendation logic."""

from datetime import datetime, timedelta

import pytest

from logic.recommendation import compare_routes
from logic.route import Route


CURRENT_TIME = datetime(2026, 11, 15, 11, 0)


def make_route(
    route_id: str,
    estimated_time: float,
    uncertainty: float,
    age_minutes: int | None,
) -> Route:
    last_updated = (
        None
        if age_minutes is None
        else CURRENT_TIME - timedelta(minutes=age_minutes)
    )
    return Route(
        route_id=route_id,
        name=f"Route {route_id}",
        estimated_time=estimated_time,
        uncertainty=uncertainty,
        last_updated=last_updated,
    )


def test_selects_route_with_lowest_estimated_time() -> None:
    result = compare_routes(
        [
            make_route("A", 35, 2, 5),
            make_route("B", 27, 10, 45),
        ],
        CURRENT_TIME,
    )

    assert result["fastest_route_id"] == "B"
    assert result["routes"][1]["minimum_time"] == 17
    assert result["routes"][1]["maximum_time"] == 37
    assert "lowest estimated journey time" in result["explanation"]


def test_selection_does_not_use_uncertainty_as_a_score() -> None:
    result = compare_routes(
        [
            make_route("A", 20, 100, 5),
            make_route("B", 25, 1, 5),
        ],
        CURRENT_TIME,
    )

    assert result["fastest_route_id"] == "A"


def test_equal_estimates_use_input_order() -> None:
    result = compare_routes(
        [
            make_route("A", 25, 2, 5),
            make_route("B", 25, 1, 5),
        ],
        CURRENT_TIME,
    )

    assert result["fastest_route_id"] == "A"


def test_single_route_is_selected() -> None:
    result = compare_routes([make_route("A", 35, 2, 5)], CURRENT_TIME)

    assert result["fastest_route_id"] == "A"
    assert len(result["routes"]) == 1


def test_empty_routes_are_rejected() -> None:
    with pytest.raises(ValueError):
        compare_routes([], CURRENT_TIME)


@pytest.mark.parametrize(
    ("age_minutes", "expected_freshness"),
    [(None, "Unavailable"), (5, "Recent"), (45, "Outdated")],
)
def test_reports_freshness(age_minutes: int | None, expected_freshness: str) -> None:
    result = compare_routes(
        [make_route("A", 35, 2, age_minutes)],
        CURRENT_TIME,
    )

    route_result = result["routes"][0]
    assert route_result["data_age_minutes"] == age_minutes
    assert route_result["freshness"] == expected_freshness
