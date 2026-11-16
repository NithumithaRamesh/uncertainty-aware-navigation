"""Tests for preference-sensitive recommendations."""

from datetime import datetime, timedelta, timezone

import pytest

from data.sample_routes import get_sample_routes
from logic.preference import (
    BALANCED,
    FASTEST,
    PREDICTABLE,
    RECENT_INFORMATION,
    recommend_by_preference,
)
from logic.route import Route


CURRENT_TIME = datetime(2026, 11, 16, 12, 0, tzinfo=timezone.utc)


def sample_routes() -> list[Route]:
    return get_sample_routes(CURRENT_TIME)


def test_fastest_preference_selects_route_a() -> None:
    result = recommend_by_preference(sample_routes(), FASTEST, CURRENT_TIME)

    assert result["recommended_route_id"] == "A"
    assert "lowest estimated journey time" in result["reason"]


def test_predictable_preference_selects_route_b() -> None:
    result = recommend_by_preference(sample_routes(), PREDICTABLE, CURRENT_TIME)

    assert result["recommended_route_id"] == "B"
    assert "lowest estimated uncertainty" in result["reason"]


def test_recent_information_preference_selects_route_b() -> None:
    result = recommend_by_preference(
        sample_routes(), RECENT_INFORMATION, CURRENT_TIME
    )

    assert result["recommended_route_id"] == "B"
    assert "most recently updated" in result["reason"]


def test_balanced_preference_returns_transparent_shortlist() -> None:
    result = recommend_by_preference(sample_routes(), BALANCED, CURRENT_TIME)

    assert result["recommended_route_id"] is None
    assert result["shortlist_route_ids"]
    assert "arbitrary weighted score" in result["explanation"]


def test_empty_routes_are_rejected() -> None:
    with pytest.raises(ValueError):
        recommend_by_preference([], FASTEST, CURRENT_TIME)


def test_duplicate_route_ids_are_rejected() -> None:
    routes = sample_routes()
    routes.append(routes[0])

    with pytest.raises(ValueError, match="unique route_id"):
        recommend_by_preference(routes, FASTEST, CURRENT_TIME)


def test_recent_information_excludes_missing_timestamps() -> None:
    routes = [
        Route("A", "Route A", 20, 2, None),
        Route(
            "B",
            "Route B",
            25,
            3,
            CURRENT_TIME - timedelta(minutes=5),
        ),
    ]

    result = recommend_by_preference(routes, RECENT_INFORMATION, CURRENT_TIME)

    assert result["recommended_route_id"] == "B"


def test_recent_information_returns_shortlist_when_all_timestamps_missing() -> None:
    routes = [
        Route("A", "Route A", 20, 2, None),
        Route("B", "Route B", 25, 3, None),
    ]

    result = recommend_by_preference(routes, RECENT_INFORMATION, CURRENT_TIME)

    assert result["recommended_route_id"] is None
    assert result["shortlist_route_ids"] == ["A", "B"]


def test_equal_estimates_use_route_id_for_deterministic_tie_breaking() -> None:
    routes = [
        Route("B", "Route B", 20, 2, CURRENT_TIME),
        Route("A", "Route A", 20, 2, CURRENT_TIME),
    ]

    result = recommend_by_preference(routes, FASTEST, CURRENT_TIME)

    assert result["recommended_route_id"] == "A"


def test_invalid_preference_is_rejected() -> None:
    with pytest.raises(ValueError, match="Unsupported preference"):
        recommend_by_preference(sample_routes(), "UNKNOWN", CURRENT_TIME)


def test_naive_current_time_is_rejected() -> None:
    with pytest.raises(TypeError, match="timezone-aware"):
        recommend_by_preference(
            sample_routes(),
            FASTEST,
            datetime(2026, 11, 16, 12, 0),
        )
