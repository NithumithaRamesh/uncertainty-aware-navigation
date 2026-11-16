"""Journey-duration and simulated-uncertainty trade-off comparisons."""

from typing import TypedDict

from .route import Route
from .uncertainty import calculate_time_range


class TradeoffResult(TypedDict):
    """Structured values used to explain a two-criterion route trade-off."""

    fastest_route_id: str
    predictable_route_id: str
    fastest_estimated_time: float
    predictable_estimated_time: float
    fastest_uncertainty: float
    predictable_uncertainty: float
    fastest_minimum_time: float
    fastest_maximum_time: float
    predictable_minimum_time: float
    predictable_maximum_time: float
    estimated_time_difference: float
    uncertainty_difference: float
    same_route: bool
    explanation: str


def compare_route_tradeoff(routes: list[Route]) -> TradeoffResult:
    """Compare the fastest and most predictable available routes.

    Duration and uncertainty remain separate criteria. No weighted score or
    threshold is used. Ties are resolved by route ID to keep the result
    deterministic.

    Raises:
        ValueError: If routes is empty, or route IDs are duplicated.
        TypeError: If routes contains a non-Route value.
    """
    if not routes:
        raise ValueError("routes must contain at least one route")
    if any(not isinstance(route, Route) for route in routes):
        raise TypeError("routes must contain only Route instances")
    route_ids = [route.route_id for route in routes]
    if len(route_ids) != len(set(route_ids)):
        raise ValueError("routes must have unique route_id values")

    fastest_route = min(
        routes,
        key=lambda route: (route.estimated_time, route.route_id),
    )
    predictable_route = min(
        routes,
        key=lambda route: (route.uncertainty, route.route_id),
    )
    fastest_minimum, fastest_maximum = calculate_time_range(fastest_route)
    predictable_minimum, predictable_maximum = calculate_time_range(
        predictable_route
    )
    estimated_time_difference = (
        predictable_route.estimated_time - fastest_route.estimated_time
    )
    uncertainty_difference = (
        fastest_route.uncertainty - predictable_route.uncertainty
    )
    same_route = fastest_route.route_id == predictable_route.route_id

    return {
        "fastest_route_id": fastest_route.route_id,
        "predictable_route_id": predictable_route.route_id,
        "fastest_estimated_time": fastest_route.estimated_time,
        "predictable_estimated_time": predictable_route.estimated_time,
        "fastest_uncertainty": fastest_route.uncertainty,
        "predictable_uncertainty": predictable_route.uncertainty,
        "fastest_minimum_time": fastest_minimum,
        "fastest_maximum_time": fastest_maximum,
        "predictable_minimum_time": predictable_minimum,
        "predictable_maximum_time": predictable_maximum,
        "estimated_time_difference": estimated_time_difference,
        "uncertainty_difference": uncertainty_difference,
        "same_route": same_route,
        "explanation": _build_explanation(
            fastest_route,
            predictable_route,
            estimated_time_difference,
            uncertainty_difference,
        ),
    }


def _build_explanation(
    fastest_route: Route,
    predictable_route: Route,
    estimated_time_difference: float,
    uncertainty_difference: float,
) -> str:
    if fastest_route.route_id == predictable_route.route_id:
        return (
            f"{fastest_route.name} has both the lowest estimated journey time "
            "and the lowest simulated uncertainty among the available routes."
        )

    fastest_name = fastest_route.name
    predictable_name = predictable_route.name
    time_difference = _format_number(estimated_time_difference)
    if estimated_time_difference == 0 and uncertainty_difference > 0:
        return (
            f"{fastest_name} and {predictable_name} have the same estimated "
            f"journey time, but {predictable_name} has a narrower simulated "
            f"uncertainty range (±{_format_number(predictable_route.uncertainty)} "
            f"minutes versus ±{_format_number(fastest_route.uncertainty)} "
            f"minutes for {fastest_name})."
        )
    if uncertainty_difference > 0:
        return (
            f"{fastest_name} is approximately {time_difference} minutes faster, "
            f"but {predictable_name} has a narrower simulated uncertainty range "
            f"(±{_format_number(predictable_route.uncertainty)} minutes versus "
            f"±{_format_number(fastest_route.uncertainty)} minutes for "
            f"{fastest_name})."
        )
    if estimated_time_difference == 0:
        return (
            f"{fastest_name} and {predictable_name} have the same estimated "
            "journey time, while their simulated uncertainty is also tied."
        )
    return (
        f"{fastest_name} is approximately {time_difference} minutes faster, "
        f"while {fastest_name} and {predictable_name} have the same simulated "
        "uncertainty."
    )


def _format_number(value: float) -> str:
    """Format explanation values without unnecessary trailing zeroes."""
    return f"{value:g}"
