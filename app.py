"""Streamlit interface for the uncertainty-aware navigation prototype."""

from datetime import datetime, timezone

import streamlit as st
import plotly.graph_objects as go

from data.sample_routes import get_sample_routes
from logic.recommendation import compare_routes


FRESHNESS_INDICATORS = {
    "Recent": "🟢",
    "Moderately old": "🟡",
    "Outdated": "🔴",
    "Unavailable": "⚪",
}


def display_freshness(freshness: str, data_age_minutes: float | None) -> None:
    """Display a route's freshness classification and data age."""
    indicator = FRESHNESS_INDICATORS.get(freshness, "⚪")
    st.write(f"**Traffic data:** {indicator} {freshness}")
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
try:
    routes = get_sample_routes(current_time)
    comparison = compare_routes(routes, current_time)
except (TypeError, ValueError) as error:
    st.error(f"Unable to prepare the route comparison: {error}")
    st.stop()

route_results = {
    result["route_id"]: result for result in comparison["routes"]
}

st.header("Route overview")
route_columns = st.columns(len(routes))
for column, route in zip(route_columns, routes):
    route_result = route_results[route.route_id]
    with column:
        st.subheader(f"Route {route.route_id}")
        if route.route_id == comparison["fastest_route_id"]:
            st.caption("Fastest estimated route")
        st.write(f"**{route.name}**")
        st.metric("Estimated journey", f"{route_result['estimated_time']:g} min")
        st.write(f"**Uncertainty:** ±{route.uncertainty:g} min")
        st.write(
            f"**Estimated range:** {route_result['minimum_time']:g}–"
            f"{route_result['maximum_time']:g} min"
        )
        display_freshness(
            route_result["freshness"],
            route_result["data_age_minutes"],
        )

st.header("Journey-time uncertainty")
st.caption(
    "The line shows the estimated range. The marker shows the central "
    "journey-time estimate."
)
figure = go.Figure()
chart_annotations = []
for route in routes:
    route_result = route_results[route.route_id]
    color = (
        "#1f77b4"
        if route.route_id == comparison["fastest_route_id"]
        else "#7f8c8d"
    )
    figure.add_trace(
        go.Scatter(
            x=[route_result["minimum_time"], route_result["maximum_time"]],
            y=[route.name, route.name],
            mode="lines",
            line={"color": color, "width": 12},
            name=f"{route.name} range",
            hovertemplate=(
                f"<b>{route.name}</b><br>"
                f"Estimated journey: {route_result['estimated_time']:g} minutes"
                f"<br>Minimum: {route_result['minimum_time']:g} minutes"
                f"<br>Maximum: {route_result['maximum_time']:g} minutes"
                f"<br>Uncertainty: ±{route.uncertainty:g} minutes"
                "<extra></extra>"
            ),
            showlegend=False,
        )
    )
    figure.add_trace(
        go.Scatter(
            x=[route_result["estimated_time"]],
            y=[route.name],
            mode="markers",
            marker={"color": color, "size": 12, "line": {"color": "white", "width": 2}},
            name=f"{route.name} estimate",
            hovertemplate=(
                f"<b>{route.name}</b><br>"
                f"Estimated journey: {route_result['estimated_time']:g} minutes"
                f"<br>Minimum: {route_result['minimum_time']:g} minutes"
                f"<br>Maximum: {route_result['maximum_time']:g} minutes"
                f"<br>Uncertainty: ±{route.uncertainty:g} minutes"
                "<extra></extra>"
            ),
            showlegend=False,
        )
    )
    for time_value, y_shift in (
        (route_result["minimum_time"], -18),
        (route_result["estimated_time"], 18),
        (route_result["maximum_time"], -18),
    ):
        chart_annotations.append(
            {
                "x": time_value,
                "y": route.name,
                "xref": "x",
                "yref": "y",
                "text": f"{time_value:g}",
                "showarrow": False,
                "yshift": y_shift,
                "font": {"color": color, "size": 12},
                "bgcolor": "white",
            }
        )

figure.update_layout(
    title="Estimated Journey-Time Ranges",
    height=190,
    margin={"l": 20, "r": 20, "t": 45, "b": 35},
    xaxis={
        "title": "Journey time (minutes)",
        "showgrid": True,
        "zeroline": False,
        "showline": False,
        "ticks": "outside",
    },
    yaxis={
        "title": None,
        "categoryorder": "array",
        "categoryarray": [route.name for route in routes],
        "automargin": True,
    },
    annotations=chart_annotations,
)
st.plotly_chart(figure, width="stretch")

st.header("System recommendation")
st.success(f"Fastest estimated route: Route {comparison['fastest_route_id']}")
st.write(comparison["explanation"])
st.caption(
    "The recommendation is based on estimated journey time. "
    "The final route decision remains with the user."
)

st.header("Choose Your Route")
route_by_id = {route.route_id: route for route in routes}
selected_route_id = st.radio(
    "Select the route you want to take:",
    options=[route.route_id for route in routes],
    format_func=lambda route_id: route_by_id[route_id].name,
    index=None,
    key="selected_route_id",
)

if selected_route_id is None:
    st.info("Choose a route to confirm your selection.")
else:
    selected_route = route_by_id[selected_route_id]
    selected_result = route_results[selected_route_id]
    st.success(f"You selected Route {selected_route_id}: {selected_route.name}")
    st.write(
        f"**Estimated journey:** {selected_result['estimated_time']:g} minutes"
    )
    st.write(
        f"**Estimated range:** {selected_result['minimum_time']:g}–"
        f"{selected_result['maximum_time']:g} minutes"
    )
    display_freshness(
        selected_result["freshness"],
        selected_result["data_age_minutes"],
    )
