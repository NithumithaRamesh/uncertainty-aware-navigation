"""Traffic-data freshness assessment."""

from datetime import datetime, timezone


def assess_freshness(
    last_updated: datetime | None,
    current_time: datetime | None,
) -> tuple[float | None, str]:
    """Return the traffic-data age in minutes and its freshness classification.

    If ``last_updated`` is unavailable, the age is ``None`` and the
    classification is ``"Unavailable"`` so one incomplete route does not
    prevent the application from displaying other routes.
    Naive timestamps are compared as naive values. Timezone-aware timestamps
    are converted to UTC before comparison. Mixing naive and timezone-aware
    timestamps is rejected because their relationship is ambiguous.

    Raises:
        TypeError: If ``current_time`` is missing or either supplied value is
            not a ``datetime``.
        ValueError: If timestamp awareness differs or current time precedes
            the update time.
    """
    if current_time is None:
        raise TypeError("current_time is required")

    if not isinstance(current_time, datetime):
        raise TypeError("current_time must be a datetime value")

    if last_updated is None:
        return None, "Unavailable"

    if not isinstance(last_updated, datetime):
        raise TypeError("last_updated must be a datetime value")

    last_updated_is_aware = last_updated.tzinfo is not None
    current_time_is_aware = current_time.tzinfo is not None
    if last_updated_is_aware != current_time_is_aware:
        raise ValueError(
            "last_updated and current_time must both be naive or timezone-aware"
        )

    if last_updated_is_aware:
        last_updated = last_updated.astimezone(timezone.utc)
        current_time = current_time.astimezone(timezone.utc)

    age_minutes = (current_time - last_updated).total_seconds() / 60
    if age_minutes < 0:
        raise ValueError("current_time cannot be earlier than last_updated")

    if age_minutes <= 10:
        classification = "Recent"
    elif age_minutes <= 30:
        classification = "Moderately old"
    else:
        classification = "Outdated"

    return age_minutes, classification
