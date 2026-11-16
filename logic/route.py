"""Route data model for the navigation prototype."""

from dataclasses import dataclass
from datetime import datetime
import math


@dataclass
class Route:
    """Store the simulated estimates and traffic metadata for one route."""

    route_id: str
    name: str
    estimated_time: float
    uncertainty: float
    last_updated: datetime | None

    def __post_init__(self) -> None:
        if not isinstance(self.route_id, str) or not self.route_id.strip():
            raise ValueError("route_id must not be empty")
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("name must not be empty")
        if not isinstance(self.estimated_time, (int, float)) or isinstance(
            self.estimated_time, bool
        ):
            raise TypeError("estimated_time must be a number")
        if not math.isfinite(self.estimated_time) or self.estimated_time <= 0:
            raise ValueError("estimated_time must be greater than zero")
        if not isinstance(self.uncertainty, (int, float)) or isinstance(
            self.uncertainty, bool
        ):
            raise TypeError("uncertainty must be a number")
        if not math.isfinite(self.uncertainty) or self.uncertainty < 0:
            raise ValueError("uncertainty must be non-negative")
        if self.last_updated is not None and not isinstance(
            self.last_updated, datetime
        ):
            raise TypeError("last_updated must be a datetime or None")
