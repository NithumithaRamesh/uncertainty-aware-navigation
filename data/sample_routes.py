"""Simulated route data for the navigation prototype."""

from datetime import datetime, timedelta, timezone

from logic.route import Route


def get_sample_routes(current_time: datetime | None = None) -> list[Route]:
    """Return five simulated routes relative to the supplied UTC time."""
    if current_time is None:
        current_time = datetime.now(timezone.utc)
    if current_time.tzinfo is None:
        raise ValueError("current_time must be timezone-aware")
    current_time = current_time.astimezone(timezone.utc)

    return [
        Route(
            route_id="A",
            name="Route A",
            estimated_time=27,
            uncertainty=10,
            last_updated=current_time - timedelta(minutes=45),
        ),
        Route(
            route_id="B",
            name="Route B",
            estimated_time=35,
            uncertainty=2,
            last_updated=current_time - timedelta(minutes=5),
        ),
        Route(
            route_id="C",
            name="Route C",
            estimated_time=32,
            uncertainty=3,
            last_updated=current_time - timedelta(minutes=8),
        ),
        Route(
            route_id="D",
            name="Route D",
            estimated_time=29,
            uncertainty=5,
            last_updated=current_time - timedelta(minutes=18),
        ),
        Route(
            route_id="E",
            name="Route E",
            estimated_time=38,
            uncertainty=4,
            last_updated=current_time - timedelta(minutes=22),
        ),
    ]
