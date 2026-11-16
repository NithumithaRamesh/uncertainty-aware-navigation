"""Preference-sensitive route recommendation strategies."""

from datetime import datetime
from typing import TypedDict

from .recommendation import RouteComparison, compare_routes
from .route import Route

FASTEST = "FASTEST"
PREDICTABLE = "PREDICTABLE"
RECENT_INFORMATION = "RECENT_INFORMATION"
BALANCED = "BALANCED"

SUPPORTED_PREFERENCES = {
    FASTEST,
    PREDICTABLE,
    RECENT_INFORMATION,
    BALANCED,
}


class PreferenceRecommendation(TypedDict):
    """Structured output for a preference-sensitive recommendation."""

    preference: str
    recommended_route_id: str | None
    shortlist_route_ids: list[str]
    reason: str
    explanation: str
    routes: list[RouteComparison]


def recommend_by_preference(
    routes: list[Route],
    preference: str,
    current_time: datetime,
) -> PreferenceRecommendation:
    """Recommend routes according to an explicit user preference.

    ``FASTEST``, ``PREDICTABLE`` and ``RECENT_INFORMATION`` each select one
    route using a single transparent criterion. ``BALANCED`` returns the
    non-dominated routes instead of combining criteria into an unsupported
    weighted score.

    Raises:
        ValueError: If routes are empty, route IDs are duplicated, or the
            preference is unsupported.
        TypeError: If ``current_time`` is not a timezone-aware datetime.
    """
    if preference not in SUPPORTED_PREFERENCES:
        supported = ", ".join(sorted(SUPPORTED_PREFERENCES))
        raise ValueError(
            f"Unsupported preference {preference!r}. Choose one of: {supported}"
        )
    if not isinstance(current_time, datetime) or current_time.utcoffset() is None:
        raise TypeError("current_time must be a timezone-aware datetime")

    comparison = compare_routes(routes, current_time)
    details_by_id = {
        detail["route_id"]: detail for detail in comparison["routes"]
    }

    if preference == FASTEST:
        selected_route = min(
            routes,
            key=lambda route: (
                route.estimated_time,
                route.uncertainty,
                route.route_id,
            ),
        )
        reason = "it has the lowest estimated journey time"
        explanation = _single_route_explanation(
            selected_route, details_by_id, preference, reason
        )
        return _build_result(
            preference,
            selected_route.route_id,
            [],
            reason,
            explanation,
            comparison["routes"],
        )

    if preference == PREDICTABLE:
        selected_route = min(
            routes,
            key=lambda route: (
                route.uncertainty,
                route.estimated_time,
                route.route_id,
            ),
        )
        reason = "it has the lowest estimated uncertainty"
        explanation = _single_route_explanation(
            selected_route, details_by_id, preference, reason
        )
        return _build_result(
            preference,
            selected_route.route_id,
            [],
            reason,
            explanation,
            comparison["routes"],
        )

    if preference == RECENT_INFORMATION:
        available_routes = [
            route
            for route in routes
            if details_by_id[route.route_id]["data_age_minutes"] is not None
        ]
        if not available_routes:
            route_ids = [route.route_id for route in routes]
            explanation = (
                "No route has available traffic-data timestamps, so the "
                "system cannot identify a most recently updated route. "
                f"Available routes for review: {', '.join(route_ids)}."
            )
            return _build_result(
                preference,
                None,
                route_ids,
                "no traffic-data timestamps are available",
                explanation,
                comparison["routes"],
            )

        selected_route = min(
            available_routes,
            key=lambda route: (
                details_by_id[route.route_id]["data_age_minutes"],
                route.estimated_time,
                route.route_id,
            ),
        )
        reason = "it has the most recently updated traffic information"
        explanation = _single_route_explanation(
            selected_route, details_by_id, preference, reason
        )
        return _build_result(
            preference,
            selected_route.route_id,
            [],
            reason,
            explanation,
            comparison["routes"],
        )

    shortlist = [
        route
        for route in routes
        if not any(
            _dominates(
                other,
                route,
                details_by_id,
            )
            for other in routes
            if other.route_id != route.route_id
        )
    ]
    shortlist_ids = [route.route_id for route in shortlist]
    shortlist_summaries = "; ".join(
        _route_summary(route, details_by_id[route.route_id])
        for route in shortlist
    )
    reason = "no single route is selected because the criteria are not combined"
    explanation = (
        "Balanced comparison does not use an arbitrary weighted score or "
        "claim an objectively best route. The non-dominated shortlist is: "
        f"{shortlist_summaries}"
    )
    return _build_result(
        preference,
        None,
        shortlist_ids,
        reason,
        explanation,
        comparison["routes"],
    )


def _build_result(
    preference: str,
    recommended_route_id: str | None,
    shortlist_route_ids: list[str],
    reason: str,
    explanation: str,
    route_details: list[RouteComparison],
) -> PreferenceRecommendation:
    return {
        "preference": preference,
        "recommended_route_id": recommended_route_id,
        "shortlist_route_ids": shortlist_route_ids,
        "reason": reason,
        "explanation": explanation,
        "routes": route_details,
    }


def _single_route_explanation(
    route: Route,
    details_by_id: dict[str, RouteComparison],
    preference: str,
    reason: str,
) -> str:
    detail = details_by_id[route.route_id]
    return (
        f"{preference.title().replace('_', ' ')} preference selected "
        f"{route.name} because {reason}. {_route_summary(route, detail)} "
        "Freshness describes information age and does not guarantee accuracy."
    )


def _route_summary(route: Route, detail: RouteComparison) -> str:
    age = detail["data_age_minutes"]
    age_text = (
        "traffic-data age unavailable"
        if age is None
        else f"traffic data {age:g} minutes old"
    )
    return (
        f"{route.name}: estimated journey {detail['estimated_time']:g} minutes, "
        f"range {detail['minimum_time']:g}–{detail['maximum_time']:g} minutes, "
        f"uncertainty ±{route.uncertainty:g} minutes, "
        f"freshness {detail['freshness']} ({age_text})"
    )


def _dominates(
    candidate: Route,
    other: Route,
    details_by_id: dict[str, RouteComparison],
) -> bool:
    """Return whether candidate is no worse on all independent criteria."""
    candidate_age = details_by_id[candidate.route_id]["data_age_minutes"]
    other_age = details_by_id[other.route_id]["data_age_minutes"]
    candidate_age_value = float("inf") if candidate_age is None else candidate_age
    other_age_value = float("inf") if other_age is None else other_age

    candidate_values = (
        candidate.estimated_time,
        candidate.uncertainty,
        candidate_age_value,
    )
    other_values = (
        other.estimated_time,
        other.uncertainty,
        other_age_value,
    )
    return (
        all(candidate_value <= other_value for candidate_value, other_value in zip(
            candidate_values, other_values
        ))
        and any(candidate_value < other_value for candidate_value, other_value in zip(
            candidate_values, other_values
        ))
    )
