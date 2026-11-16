"""UK city geocoding through the OpenStreetMap Nominatim API."""

from dataclasses import dataclass
from functools import lru_cache
import math
import threading
import time
from typing import Any

import requests


NOMINATIM_SEARCH_URL = "https://nominatim.openstreetmap.org/search"
APPLICATION_USER_AGENT = "uncertainty-aware-navigation/1.0"
REQUEST_TIMEOUT_SECONDS = 10
MIN_REQUEST_INTERVAL_SECONDS = 1.0
MAX_CACHED_SEARCHES = 128

_request_lock = threading.Lock()
_last_request_time = 0.0


class GeocodingError(Exception):
    """Base error for geocoding failures."""


class GeocodingConnectionError(GeocodingError):
    """Raised when Nominatim cannot be reached."""


class GeocodingTimeoutError(GeocodingError):
    """Raised when Nominatim does not respond before the timeout."""


class GeocodingHTTPError(GeocodingError):
    """Raised when Nominatim returns an HTTP error."""


class InvalidGeocodingResponseError(GeocodingError):
    """Raised when Nominatim returns an unexpected response shape."""


@dataclass(frozen=True)
class GeocodedPlace:
    """A UK settlement returned by the geocoding service."""

    name: str
    display_name: str
    latitude: float
    longitude: float
    osm_type: str
    osm_id: int


def search_cities(city_name: str) -> list[GeocodedPlace]:
    """Search for matching UK cities and settlements.

    Results are cached by normalized city name. Empty results are returned as
    an empty list; transport, HTTP, and malformed-response failures raise a
    specific ``GeocodingError`` subclass.
    """
    if not isinstance(city_name, str) or not city_name.strip():
        raise ValueError("city_name must contain a non-empty city name")

    normalized_name = " ".join(city_name.split()).casefold()
    return _search_cities_cached(normalized_name)


@lru_cache(maxsize=MAX_CACHED_SEARCHES)
def _search_cities_cached(city_name: str) -> list[GeocodedPlace]:
    response = _request_search(city_name)
    try:
        payload = response.json()
    except ValueError as error:
        raise InvalidGeocodingResponseError(
            "Nominatim returned invalid JSON"
        ) from error

    if not isinstance(payload, list):
        raise InvalidGeocodingResponseError(
            "Nominatim response must be a JSON list"
        )

    return [_parse_place(item) for item in payload]


def _request_search(city_name: str) -> requests.Response:
    global _last_request_time

    with _request_lock:
        elapsed = time.monotonic() - _last_request_time
        if elapsed < MIN_REQUEST_INTERVAL_SECONDS:
            time.sleep(MIN_REQUEST_INTERVAL_SECONDS - elapsed)
        try:
            response = requests.get(
                NOMINATIM_SEARCH_URL,
                params={
                    "q": city_name,
                    "format": "jsonv2",
                    "countrycodes": "gb",
                    "featuretype": "settlement",
                    "addressdetails": 1,
                    "limit": 5,
                },
                headers={"User-Agent": APPLICATION_USER_AGENT},
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
        except requests.Timeout as error:
            raise GeocodingTimeoutError(
                "The geocoding request timed out"
            ) from error
        except requests.ConnectionError as error:
            raise GeocodingConnectionError(
                "Could not connect to the geocoding service"
            ) from error
        finally:
            _last_request_time = time.monotonic()

    try:
        response.raise_for_status()
    except requests.HTTPError as error:
        raise GeocodingHTTPError(
            f"Geocoding service returned HTTP {response.status_code}"
        ) from error
    return response


def _parse_place(item: Any) -> GeocodedPlace:
    if not isinstance(item, dict):
        raise InvalidGeocodingResponseError(
            "Each geocoding result must be an object"
        )

    try:
        name = _required_string(item, "name")
        display_name = _required_string(item, "display_name")
        osm_type = _required_string(item, "osm_type")
        latitude = _finite_float(item, "lat")
        longitude = _finite_float(item, "lon")
        osm_id = int(item["osm_id"])
    except (KeyError, TypeError, ValueError) as error:
        raise InvalidGeocodingResponseError(
            "A geocoding result is missing valid place fields"
        ) from error

    return GeocodedPlace(
        name=name,
        display_name=display_name,
        latitude=latitude,
        longitude=longitude,
        osm_type=osm_type,
        osm_id=osm_id,
    )


def _required_string(item: dict[str, Any], key: str) -> str:
    value = item[key]
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a non-empty string")
    return value.strip()


def _finite_float(item: dict[str, Any], key: str) -> float:
    value = float(item[key])
    if not math.isfinite(value):
        raise ValueError(f"{key} must be finite")
    return value
