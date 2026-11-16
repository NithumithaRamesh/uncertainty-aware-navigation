"""Simulated route data for the navigation prototype."""

from datetime import datetime, timedelta, timezone

from logic.route import Route


def get_sample_routes(current_time: datetime | None = None) -> list[Route]:
    """Return two simulated routes relative to the supplied UTC time."""
    if current_time is None:
        current_time = datetime.now(timezone.utc)
    if current_time.tzinfo is None:
        raise ValueError("current_time must be timezone-aware")

    return [
        Route(
            route_id="A",
            name="M6",
            estimated_time=35,
            uncertainty=2,
            last_updated=current_time - timedelta(minutes=5),
        ),
        Route(
            route_id="B",
            name="Alternative route",
            estimated_time=27,
            uncertainty=10,
            last_updated=current_time - timedelta(minutes=45),
        ),
    ]
