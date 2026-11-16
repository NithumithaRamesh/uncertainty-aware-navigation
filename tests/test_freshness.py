"""Tests for traffic-data freshness assessment."""

from datetime import datetime, timedelta, timezone

import pytest

from logic.freshness import assess_freshness


def test_classifies_freshness_thresholds() -> None:
    current_time = datetime(2026, 11, 15, 11, 0)

    assert assess_freshness(current_time - timedelta(minutes=5), current_time) == (
        5.0,
        "Recent",
    )
    assert assess_freshness(current_time - timedelta(minutes=30), current_time) == (
        30.0,
        "Moderately old",
    )
    assert assess_freshness(current_time - timedelta(minutes=60), current_time) == (
        60.0,
        "Outdated",
    )


def test_handles_timezone_aware_timestamps() -> None:
    last_updated = datetime(2026, 11, 15, 10, 55, tzinfo=timezone.utc)
    current_time = datetime(
        2026, 11, 15, 6, 0, tzinfo=timezone(timedelta(hours=-5))
    )

    assert assess_freshness(last_updated, current_time) == (5.0, "Recent")


@pytest.mark.parametrize(
    ("last_updated", "current_time", "error"),
    [
        (None, datetime(2026, 11, 15, 11, 0), TypeError),
        (datetime(2026, 11, 15, 11, 0), None, TypeError),
        (
            datetime(2026, 11, 15, 10, 55),
            datetime(2026, 11, 15, 6, 0, tzinfo=timezone.utc),
            ValueError,
        ),
        (
            datetime(2026, 11, 15, 11, 0),
            datetime(2026, 11, 15, 10, 59),
            ValueError,
        ),
    ],
)
def test_rejects_invalid_timestamps(
    last_updated: datetime | None,
    current_time: datetime | None,
    error: type[Exception],
) -> None:
    with pytest.raises(error):
        assess_freshness(last_updated, current_time)
