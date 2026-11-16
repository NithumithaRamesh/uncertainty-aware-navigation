"""Deterministic illustrative uncertainty for dynamically routed journeys.

The simulator does not estimate real traffic uncertainty. It assigns stable
illustrative values so the existing decision-support interface can demonstrate
uncertainty independently of OSRM. Values depend on route identity and the
configured range, not on journey duration, so a shorter route is not made
artificially more predictable.
"""

from dataclasses import dataclass, replace
import hashlib
import math
from collections.abc import Iterable

from logic.route import Route


@dataclass(frozen=True)
class UncertaintySimulationConfig:
    """Bounds for illustrative uncertainty values, in minutes."""

    minimum_minutes: float = 2.0
    maximum_minutes: float = 10.0

    def __post_init__(self) -> None:
        for name, value in (
            ("minimum_minutes", self.minimum_minutes),
            ("maximum_minutes", self.maximum_minutes),
        ):
            if (
                not isinstance(value, (int, float))
                or isinstance(value, bool)
                or not math.isfinite(value)
                or value < 0
            ):
                raise ValueError(f"{name} must be a finite non-negative number")
        if self.minimum_minutes > self.maximum_minutes:
            raise ValueError(
                "minimum_minutes must not exceed maximum_minutes"
            )


def simulate_route_uncertainty(
    routes: Iterable[Route],
    config: UncertaintySimulationConfig | None = None,
) -> list[Route]:
    """Return routes with deterministic, illustrative uncertainty values.

    A stable SHA-256 digest of each route's ID and name selects a value within
    the configured bounds. No random generator or live traffic input is used,
    so reruns produce the same result for the same route identities and
    configuration. The returned routes retain their original timestamps.
    """
    if isinstance(routes, (str, bytes)):
        raise TypeError("routes must contain Route objects")
    route_list = list(routes)
    if any(not isinstance(route, Route) for route in route_list):
        raise TypeError("routes must contain only Route objects")
    route_ids = [route.route_id for route in route_list]
    if len(route_ids) != len(set(route_ids)):
        raise ValueError("routes must have unique route IDs")

    simulation_config = (
        UncertaintySimulationConfig() if config is None else config
    )
    if not isinstance(simulation_config, UncertaintySimulationConfig):
        raise TypeError("config must be an UncertaintySimulationConfig")

    return [
        replace(
            route,
            uncertainty=_illustrative_uncertainty(route, simulation_config),
        )
        for route in route_list
    ]


def _illustrative_uncertainty(
    route: Route,
    config: UncertaintySimulationConfig,
) -> float:
    digest = hashlib.sha256(
        f"{route.route_id}\0{route.name}".encode("utf-8")
    ).digest()
    fraction = int.from_bytes(digest[:8], "big") / ((1 << 64) - 1)
    value = config.minimum_minutes + (
        fraction * (config.maximum_minutes - config.minimum_minutes)
    )
    return round(value, 2)
