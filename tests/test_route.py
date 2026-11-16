"""Tests for the Route data model."""

from datetime import datetime

import pytest

from logic.route import Route


def make_route(**overrides: object) -> Route:
    values = {
        "route_id": "A",
        "name": "M6",
        "estimated_time": 35.0,
        "uncertainty": 2.0,
        "last_updated": datetime(2026, 11, 15, 10, 55),
    }
    values.update(overrides)
    return Route(**values)


def test_creates_valid_route() -> None:
    route = make_route()

    assert route.route_id == "A"
    assert route.name == "M6"
    assert route.estimated_time == 35.0
    assert route.uncertainty == 2.0


@pytest.mark.parametrize(
    "field",
    ["route_id", "name"],
)
def test_rejects_empty_text_fields(field: str) -> None:
    with pytest.raises(ValueError):
        make_route(**{field: "  "})


@pytest.mark.parametrize("estimated_time", [0, -1])
def test_rejects_non_positive_estimated_time(estimated_time: float) -> None:
    with pytest.raises(ValueError):
        make_route(estimated_time=estimated_time)


def test_rejects_negative_uncertainty() -> None:
    with pytest.raises(ValueError):
        make_route(uncertainty=-1)
