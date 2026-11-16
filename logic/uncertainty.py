"""Travel-time uncertainty calculations."""

from .route import Route


def calculate_time_range(route: Route) -> tuple[float, float]:
    """Return the lower and upper estimated journey-time bounds for a route."""
    return (
        route.estimated_time - route.uncertainty,
        route.estimated_time + route.uncertainty,
    )
