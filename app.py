"""Streamlit interface for the uncertainty-aware navigation prototype."""

from datetime import datetime, timezone

import streamlit as st

from data.sample_routes import get_sample_routes
from logic.recommendation import compare_routes


def display_freshness(freshness: str, data_age_minutes: float | None) -> None:
    """Display a route's freshness classification and data age."""
    st.write(f"**Traffic data:** {freshness}")
    if data_age_minutes is None:
        st.caption("Update time unavailable")
    else:
        st.caption(f"Updated {data_age_minutes:g} minutes ago")


st.set_page_config(
    page_title="Uncertainty-Aware Navigation",
    layout="wide",
)
st.title("Uncertainty-Aware Navigation")
st.write(
    "Compare route estimates while keeping travel-time uncertainty and "
    "traffic-data freshness visible."
)
st.info(
    "All journey-time estimates and traffic information shown here are "
    "simulated values."
)

origin, destination = st.columns(2)
with origin:
    st.write("**Origin**")
    st.write("Birmingham")
with destination:
    st.write("**Destination**")
    st.write("Manchester")

current_time = datetime.now(timezone.utc)
routes = get_sample_routes(current_time)
comparison = compare_routes(routes, current_time)
route_results = {
    result["route_id"]: result for result in comparison["routes"]
}

st.header("Route overview")
route_columns = st.columns(len(routes))
for column, route in zip(route_columns, routes):
    route_result = route_results[route.route_id]
    with column:
        st.subheader(f"Route {route.route_id}")
        st.write(f"**{route.name}**")
        st.metric("Estimated journey", f"{route_result['estimated_time']:g} min")
        st.write(f"**Uncertainty:** ±{route.uncertainty:g} min")
        display_freshness(
            route_result["freshness"],
            route_result["data_age_minutes"],
        )

st.header("System recommendation")
st.write(comparison["explanation"])
st.caption(
    "The recommendation is based on estimated journey time. "
    "The final route decision remains with the user."
)
