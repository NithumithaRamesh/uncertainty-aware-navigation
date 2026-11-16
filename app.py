"""Streamlit interface for the uncertainty-aware navigation prototype."""

from datetime import datetime, timezone
import streamlit as st

from logic.preference import (
    BALANCED,
    FASTEST,
    PREDICTABLE,
    recommend_by_preference,
)
from logic.recommendation import compare_routes
from logic.route import Route
from logic.route_adapter import routed_routes_to_routes
from logic.tradeoff import compare_route_tradeoff
from services.geocoding import (
    GeocodedPlace,
    GeocodingError,
    search_cities,
)
from services.routing import RoutedRoute, RoutingError, get_routes
from simulation.freshness_simulator import simulate_route_freshness
from simulation.uncertainty_simulator import simulate_route_uncertainty


PREFERENCE_OPTIONS = {
    "Fastest": (
        FASTEST,
        "Prioritises the lowest estimated journey time.",
    ),
    "Most predictable": (
        PREDICTABLE,
        "Prioritises the lowest simulated uncertainty.",
    ),
    "Balanced": (
        BALANCED,
        "Shows trade-offs without selecting a single winner.",
    ),
}

ROUTE_STATE_KEYS = (
    "routes",
    "routed_routes",
    "route_distances_km",
    "route_origin",
    "route_destination",
    "journey_current_time",
    "selected_route_id",
)


def _initialize_state() -> None:
    defaults = {
        "origin_candidates": [],
        "destination_candidates": [],
        "origin_query": "",
        "destination_query": "",
        "recommendation_preference_label": "Fastest",
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)
    if st.session_state["recommendation_preference_label"] not in PREFERENCE_OPTIONS:
        st.session_state["recommendation_preference_label"] = "Fastest"


def _clear_route_results() -> None:
    for key in ROUTE_STATE_KEYS:
        st.session_state.pop(key, None)


def _clear_location_results() -> None:
    st.session_state["origin_candidates"] = []
    st.session_state["destination_candidates"] = []
    st.session_state.pop("origin_candidate_index", None)
    st.session_state.pop("destination_candidate_index", None)


def _same_place(origin: GeocodedPlace, destination: GeocodedPlace) -> bool:
    return (
        origin.osm_type == destination.osm_type
        and origin.osm_id == destination.osm_id
    )


def _location_label(place: GeocodedPlace) -> str:
    return f"{place.name} — {place.display_name}"


def _process_journey_search(
    origin_query: str,
    destination_query: str,
) -> None:
    """Resolve both city inputs and store candidates without routing yet."""
    _clear_route_results()
    _clear_location_results()
    origin_query = origin_query.strip()
    destination_query = destination_query.strip()
    st.session_state["origin_query"] = origin_query
    st.session_state["destination_query"] = destination_query

    if not origin_query or not destination_query:
        st.error("Enter both an origin city and a destination city.")
        return
    if origin_query.casefold() == destination_query.casefold():
        st.error("Origin and destination must be different cities.")
        return

    try:
        origin_candidates = search_cities(origin_query)
        destination_candidates = search_cities(destination_query)
    except (GeocodingError, ValueError) as error:
        st.error(f"Could not resolve the journey locations: {error}")
        return

    if not origin_candidates:
        st.error(f"No UK city found for origin: {origin_query}.")
        return
    if not destination_candidates:
        st.error(f"No UK city found for destination: {destination_query}.")
        return

    st.session_state["origin_candidates"] = origin_candidates
    st.session_state["destination_candidates"] = destination_candidates
    if len(origin_candidates) == 1 and len(destination_candidates) == 1:
        _process_route_retrieval(origin_candidates[0], destination_candidates[0])
        return
    st.success("Choose the intended location before retrieving routes.")


def _process_route_retrieval(
    origin: GeocodedPlace,
    destination: GeocodedPlace,
) -> None:
    """Retrieve, adapt, and simulate routes for the selected places."""
    _clear_route_results()
    if _same_place(origin, destination):
        st.error("Origin and destination resolve to the same location.")
        return

    current_time = datetime.now(timezone.utc)
    try:
        routed_routes, routes = _retrieve_route_data(
            origin,
            destination,
            current_time,
        )
    except (RoutingError, TypeError, ValueError) as error:
        st.error(f"Could not retrieve routes: {error}")
        return

    st.session_state["routes"] = routes
    st.session_state["routed_routes"] = routed_routes
    st.session_state["route_distances_km"] = {
        route.route_id: route.distance_km for route in routed_routes
    }
    st.session_state["route_origin"] = origin
    st.session_state["route_destination"] = destination
    st.session_state["journey_current_time"] = current_time
    st.success(f"{len(routes)} route(s) retrieved. No routes were fabricated.")


def _retrieve_route_data(
    origin: GeocodedPlace,
    destination: GeocodedPlace,
    current_time: datetime | None = None,
) -> tuple[list[RoutedRoute], list[Route]]:
    """Fetch external routes and add the prototype's simulated metadata."""
    if current_time is None:
        current_time = datetime.now(timezone.utc)
    routed_routes = get_routes(origin, destination)
    routes = routed_routes_to_routes(routed_routes)
    routes = simulate_route_freshness(routes, current_time)
    routes = simulate_route_uncertainty(
        routes
    )
    return routed_routes, routes


def _render_journey_input() -> None:
    st.header("Plan a journey")
    with st.form("journey_form"):
        columns = st.columns(2)
        with columns[0]:
            origin_query = st.text_input(
                "Origin city (UK)",
                key="origin_input",
                placeholder="e.g. Birmingham",
            )
        with columns[1]:
            destination_query = st.text_input(
                "Destination city (UK)",
                key="destination_input",
                placeholder="e.g. Manchester",
            )
        submitted = st.form_submit_button("Find Routes")
    if submitted:
        _process_journey_search(origin_query, destination_query)


def _render_location_resolution() -> None:
    origin_candidates = st.session_state["origin_candidates"]
    destination_candidates = st.session_state["destination_candidates"]
    if (
        not origin_candidates
        or not destination_candidates
        or (len(origin_candidates) == 1 and len(destination_candidates) == 1)
    ):
        return

    st.subheader("Confirm locations")
    columns = st.columns(2)
    with columns[0]:
        if len(origin_candidates) == 1:
            origin_index = 0
            st.caption(f"Origin: {_location_label(origin_candidates[0])}")
        else:
            origin_index = st.selectbox(
                "Origin result",
                options=range(len(origin_candidates)),
                format_func=lambda index: _location_label(origin_candidates[index]),
                key="origin_candidate_index",
            )
    with columns[1]:
        if len(destination_candidates) == 1:
            destination_index = 0
            st.caption(
                f"Destination: {_location_label(destination_candidates[0])}"
            )
        else:
            destination_index = st.selectbox(
                "Destination result",
                options=range(len(destination_candidates)),
                format_func=lambda index: _location_label(destination_candidates[index]),
                key="destination_candidate_index",
            )

    if st.button("Retrieve routes", type="primary"):
        _process_route_retrieval(
            origin_candidates[origin_index],
            destination_candidates[destination_index],
        )


def _render_route_results() -> None:
    routes: list[Route] = st.session_state["routes"]
    current_time: datetime = st.session_state["journey_current_time"]
    route_distances_km: dict[str, float] = st.session_state["route_distances_km"]
    comparison = compare_routes(routes, current_time)
    route_results = {
        result["route_id"]: result for result in comparison["routes"]
    }
    route_by_id = {route.route_id: route for route in routes}

    origin: GeocodedPlace = st.session_state["route_origin"]
    destination: GeocodedPlace = st.session_state["route_destination"]
    st.caption(
        f"{_location_label(origin)} → {_location_label(destination)}"
    )

    preference_label = st.radio(
        "Preference",
        options=list(PREFERENCE_OPTIONS),
        horizontal=True,
        key="recommendation_preference_label",
    )
    preference, description = PREFERENCE_OPTIONS[preference_label]
    st.caption(description)
    preference_result = recommend_by_preference(
        routes,
        preference,
        current_time,
    )
    tradeoff = compare_route_tradeoff(routes)
    st.caption(tradeoff["explanation"])
    highlighted_route_ids = (
        set(preference_result["shortlist_route_ids"])
        if preference_result["recommended_route_id"] is None
        else {preference_result["recommended_route_id"]}
    )

    route_by_id = {route.route_id: route for route in routes}
    ordered_routes = [
        route
        for route in routes
        if route.route_id in highlighted_route_ids
    ] + [
        route
        for route in routes
        if route.route_id not in highlighted_route_ids
    ]

    st.subheader("Routes")
    columns = st.columns(len(ordered_routes))
    for column, route in zip(columns, ordered_routes):
        result = route_results[route.route_id]
        with column.container(border=True):
            st.markdown(f"#### Route {route.route_id}")
            if route.route_id in highlighted_route_ids:
                label = (
                    "Balanced shortlist"
                    if preference == BALANCED
                    else "Recommended for selected preference"
                )
                st.caption(f"**{label}**")
            st.metric(
                "Journey",
                f"{_format_value(result['estimated_time'])} min",
            )
            st.write(
                f"**Distance:** "
                f"{_format_value(route_distances_km[route.route_id])} km"
            )
            st.write(
                f"**Uncertainty:** ±{_format_value(route.uncertainty)} min"
            )
            st.write(
                f"**Range:** {_format_value(result['minimum_time'])}–"
                f"{_format_value(result['maximum_time'])} min"
            )
            data_age = result["data_age_minutes"]
            if data_age is None:
                st.write("**Traffic data:** Unavailable")
            else:
                st.write(
                    f"**Traffic data:** {result['freshness']} "
                    f"({_format_value(data_age)} min old)"
                )
            if st.button(
                "Select route",
                key=f"select_route_{route.route_id}",
            ):
                st.session_state["selected_route_id"] = route.route_id

    selected_route_id = st.session_state.get("selected_route_id")
    if selected_route_id is None:
        st.caption("Select a route to confirm your choice.")
    elif selected_route_id in route_by_id:
        selected_route = route_by_id[selected_route_id]
        st.success(f"Selected: {selected_route.name}")

    with st.expander("View details"):
        st.write(
            "Journey durations and distances are retrieved from OSRM. "
            "Traffic-data ages are simulated illustrative conditions because "
            "OSRM does not provide traffic timestamps. "
            "The displayed range is an illustrative uncertainty range around "
            "the estimate; it is simulated and not an empirically calibrated "
            "confidence interval."
        )
        st.write(
            "This demonstrates a decision-support interaction, not a validated "
            "improvement in driver trust or route-selection behaviour."
        )


def _format_value(value: float) -> str:
    """Format a displayed measurement with at most one decimal place."""
    return f"{value:.1f}".rstrip("0").rstrip(".")


def main() -> None:
    st.set_page_config(
        page_title="Uncertainty-Aware Navigation",
        layout="wide",
    )
    _initialize_state()
    st.title("Uncertainty-Aware Navigation")
    _render_journey_input()
    _render_location_resolution()
    if "routes" not in st.session_state:
        st.info("Enter two UK cities and choose Find Routes to begin.")
        return
    _render_route_results()


if __name__ == "__main__":
    main()
