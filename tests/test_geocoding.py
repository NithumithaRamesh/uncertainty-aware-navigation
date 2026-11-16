"""Tests for the Nominatim geocoding service."""

from unittest.mock import Mock, patch

import pytest
import requests

from services import geocoding
from services.geocoding import (
    GeocodingConnectionError,
    GeocodingHTTPError,
    GeocodingTimeoutError,
    InvalidGeocodingResponseError,
    search_cities,
)


def setup_function() -> None:
    geocoding._search_cities_cached.cache_clear()


def nominatim_response(payload: object, status_code: int = 200) -> Mock:
    response = Mock()
    response.status_code = status_code
    response.json.return_value = payload
    if status_code >= 400:
        response.raise_for_status.side_effect = requests.HTTPError()
    return response


def test_search_parses_places_and_caches_normalized_queries() -> None:
    payload = [
        {
            "name": "Birmingham",
            "display_name": "Birmingham, West Midlands, England, United Kingdom",
            "lat": "52.4797",
            "lon": "-1.9027",
            "osm_type": "relation",
            "osm_id": 162381,
        }
    ]
    response = nominatim_response(payload)

    with patch("services.geocoding.requests.get", return_value=response) as get:
        first_result = search_cities(" Birmingham ")
        second_result = search_cities("birmingham")

    assert first_result == second_result
    assert first_result[0].latitude == 52.4797
    assert first_result[0].longitude == -1.9027
    get.assert_called_once()
    assert get.call_args.kwargs["headers"]["User-Agent"]
    assert get.call_args.kwargs["params"]["countrycodes"] == "gb"


def test_no_matches_returns_empty_list() -> None:
    with patch(
        "services.geocoding.requests.get",
        return_value=nominatim_response([]),
    ):
        assert search_cities("No Such City") == []


@pytest.mark.parametrize(
    "error",
    [
        requests.Timeout("timeout"),
        requests.ConnectionError("connection"),
    ],
)
def test_translates_request_failures(error: Exception) -> None:
    with patch("services.geocoding.requests.get", side_effect=error):
        with pytest.raises(
            GeocodingTimeoutError
            if isinstance(error, requests.Timeout)
            else GeocodingConnectionError
        ):
            search_cities("Birmingham")


def test_translates_http_failure() -> None:
    with patch(
        "services.geocoding.requests.get",
        return_value=nominatim_response({}, status_code=503),
    ):
        with pytest.raises(GeocodingHTTPError):
            search_cities("Birmingham")


@pytest.mark.parametrize(
    "payload",
    [{"name": "Birmingham"}, {"lat": "not-a-number"}, {"unexpected": True}],
)
def test_rejects_invalid_response_items(payload: dict[str, object]) -> None:
    with patch(
        "services.geocoding.requests.get",
        return_value=nominatim_response([payload]),
    ):
        with pytest.raises(InvalidGeocodingResponseError):
            search_cities("Birmingham")


def test_rejects_empty_city_name() -> None:
    with pytest.raises(ValueError):
        search_cities("  ")
