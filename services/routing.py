"""Road-route retrieval through the public OSRM routing API."""

from dataclasses import dataclass
import math
from typing import Any

import requests

from .geocoding import GeocodedPlace


OSRM_ROUTE_URL = "https://router.project-osrm.org/route/v1/driving"
REQUEST_TIMEOUT_SECONDS = 20
ROUTING_USER_AGENT = "uncertainty-aware-navigation/1.0"


class RoutingError(Exception):
    """Base error for route retrieval failures."""


class RoutingConnectionError(RoutingError):
    """Raised when OSRM cannot be reached."""


class RoutingTimeoutError(RoutingError):
    """Raised when OSRM does not respond before the timeout."""


class RoutingHTTPError(RoutingError):
    """Raised when OSRM returns an HTTP error."""


class RoutingAPIError(RoutingError):
    """Raised when OSRM reports an unsuccessful routing operation."""


class NoRouteError(RoutingAPIError):
    """Raised when OSRM cannot find a route between the places."""


class InvalidRoutingResponseError(RoutingError):
    """Raised when OSRM returns an unexpected or unusable response."""


@dataclass(frozen=True)
class RoutedRoute:
    """A route returned by OSRM, without uncertainty or freshness metadata."""

    route_id: str
    distance_metres: float
    distance_km: float
    duration_seconds: float
    duration_minutes: float
    geometry: dict[str, Any]


def get_routes(
    origin: GeocodedPlace,
    destination: GeocodedPlace,
) -> list[RoutedRoute]:
    """Retrieve all routes OSRM returns between two geocoded places."""
    if not isinstance(origin, GeocodedPlace):
        raise TypeError("origin must be a GeocodedPlace")
    if not isinstance(destination, GeocodedPlace):
        raise TypeError("destination must be a GeocodedPlace")

    response = _request_routes(origin, destination)
    try:
        payload = response.json()
    except ValueError as error:
        raise InvalidRoutingResponseError("OSRM returned invalid JSON") from error

    if not isinstance(payload, dict):
        raise InvalidRoutingResponseError("OSRM response must be a JSON object")

    response_code = payload.get("code")
    if response_code == "NoRoute":
        raise NoRouteError("OSRM could not find a route between the places")
    if response_code != "Ok":
        raise RoutingAPIError(
            f"OSRM returned routing code {response_code!r}"
        )

    raw_routes = payload.get("routes")
    if not isinstance(raw_routes, list):
        raise InvalidRoutingResponseError(
            "OSRM response must contain a routes list"
        )
    if not raw_routes:
        raise NoRouteError("OSRM returned no routes")

    return [
        _parse_route(route, index)
        for index, route in enumerate(raw_routes)
    ]


def _request_routes(
    origin: GeocodedPlace,
    destination: GeocodedPlace,
) -> requests.Response:
    coordinates = (
        f"{origin.longitude},{origin.latitude};"
        f"{destination.longitude},{destination.latitude}"
    )
    try:
        response = requests.get(
            f"{OSRM_ROUTE_URL}/{coordinates}",
            params={
                "alternatives": "true",
                "overview": "full",
                "geometries": "geojson",
                "steps": "false",
            },
            headers={"User-Agent": ROUTING_USER_AGENT},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
    except requests.Timeout as error:
        raise RoutingTimeoutError("The routing request timed out") from error
    except requests.ConnectionError as error:
        raise RoutingConnectionError(
            "Could not connect to the routing service"
        ) from error

    try:
        response.raise_for_status()
    except requests.HTTPError as error:
        raise RoutingHTTPError(
            f"Routing service returned HTTP {response.status_code}"
        ) from error
    return response


def _parse_route(raw_route: Any, index: int) -> RoutedRoute:
    if not isinstance(raw_route, dict):
        raise InvalidRoutingResponseError("Each OSRM route must be an object")

    try:
        distance_metres = _positive_number(raw_route, "distance")
        duration_seconds = _positive_number(raw_route, "duration")
        geometry = _validate_geometry(raw_route["geometry"])
    except (KeyError, TypeError, ValueError) as error:
        raise InvalidRoutingResponseError(
            "An OSRM route is missing valid distance, duration or geometry"
        ) from error

    return RoutedRoute(
        route_id=_route_id(index),
        distance_metres=distance_metres,
        distance_km=distance_metres / 1000,
        duration_seconds=duration_seconds,
        duration_minutes=duration_seconds / 60,
        geometry=geometry,
    )


def _positive_number(route: dict[str, Any], key: str) -> float:
    value = route[key]
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{key} must be a positive finite number")
    value = float(value)
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{key} must be a positive finite number")
    return value


def _validate_geometry(geometry: Any) -> dict[str, Any]:
    if not isinstance(geometry, dict):
        raise TypeError("geometry must be an object")
    if geometry.get("type") != "LineString":
        raise ValueError("geometry must be a GeoJSON LineString")

    coordinates = geometry.get("coordinates")
    if not isinstance(coordinates, list) or len(coordinates) < 2:
        raise ValueError("geometry must contain at least two coordinates")
    for coordinate in coordinates:
        if (
            not isinstance(coordinate, list)
            or len(coordinate) < 2
            or any(
                not isinstance(value, (int, float))
                or isinstance(value, bool)
                or not math.isfinite(float(value))
                for value in coordinate
            )
        ):
            raise ValueError("geometry contains an invalid coordinate")
    return geometry


def _route_id(index: int) -> str:
    """Return A, B, ..., Z, AA, AB, ... for a zero-based route index."""
    route_id = ""
    index += 1
    while index:
        index, remainder = divmod(index - 1, 26)
        route_id = chr(ord("A") + remainder) + route_id
    return route_id
