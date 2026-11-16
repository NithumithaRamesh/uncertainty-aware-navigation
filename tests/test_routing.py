"""Tests for the OSRM routing service."""

from unittest.mock import Mock, patch

import pytest
import requests

from services.geocoding import GeocodedPlace
from services.routing import (
    InvalidRoutingResponseError,
    NoRouteError,
    RoutingAPIError,
    RoutingConnectionError,
    RoutingHTTPError,
    RoutingTimeoutError,
    get_routes,
)


ORIGIN = GeocodedPlace("Birmingham", "Birmingham, UK", 52.48, -1.9, "relation", 1)
DESTINATION = GeocodedPlace(
    "Manchester", "Manchester, UK", 53.48, -2.24, "relation", 2
)
GEOMETRY = {
    "type": "LineString",
    "coordinates": [[-1.9, 52.48], [-2.24, 53.48]],
}


def osrm_response(payload: object, status_code: int = 200) -> Mock:
    response = Mock()
    response.status_code = status_code
    response.json.return_value = payload
    if status_code >= 400:
        response.raise_for_status.side_effect = requests.HTTPError()
    return response


def route_payload(distance: float = 12000, duration: float = 1800) -> dict:
    return {
        "distance": distance,
        "duration": duration,
        "geometry": GEOMETRY,
    }


def test_parses_multiple_routes_and_request_parameters() -> None:
    response = osrm_response(
        {
            "code": "Ok",
            "routes": [
                route_payload(),
                route_payload(distance=15000, duration=2100),
            ],
        }
    )

    with patch("services.routing.requests.get", return_value=response) as get:
        routes = get_routes(ORIGIN, DESTINATION)

    assert [route.route_id for route in routes] == ["A", "B"]
    assert routes[0].distance_km == 12
    assert routes[0].duration_minutes == 30
    assert routes[0].geometry == GEOMETRY
    request_url = get.call_args.args[0]
    assert request_url.endswith("-1.9,52.48;-2.24,53.48")
    assert get.call_args.kwargs["params"] == {
        "alternatives": "true",
        "overview": "full",
        "geometries": "geojson",
        "steps": "false",
    }


def test_preserves_single_route_without_fabricating_alternatives() -> None:
    with patch(
        "services.routing.requests.get",
        return_value=osrm_response({"code": "Ok", "routes": [route_payload()]}),
    ):
        routes = get_routes(ORIGIN, DESTINATION)

    assert len(routes) == 1
    assert routes[0].route_id == "A"


def test_handles_no_route_response() -> None:
    with patch(
        "services.routing.requests.get",
        return_value=osrm_response({"code": "NoRoute", "routes": []}),
    ):
        with pytest.raises(NoRouteError):
            get_routes(ORIGIN, DESTINATION)


def test_handles_other_osrm_errors() -> None:
    with patch(
        "services.routing.requests.get",
        return_value=osrm_response({"code": "InvalidQuery"}),
    ):
        with pytest.raises(RoutingAPIError):
            get_routes(ORIGIN, DESTINATION)


def test_handles_http_connection_and_timeout_errors() -> None:
    with patch(
        "services.routing.requests.get",
        return_value=osrm_response({}, status_code=500),
    ):
        with pytest.raises(RoutingHTTPError):
            get_routes(ORIGIN, DESTINATION)

    with patch(
        "services.routing.requests.get",
        side_effect=requests.ConnectionError("offline"),
    ):
        with pytest.raises(RoutingConnectionError):
            get_routes(ORIGIN, DESTINATION)

    with patch(
        "services.routing.requests.get",
        side_effect=requests.Timeout("slow"),
    ):
        with pytest.raises(RoutingTimeoutError):
            get_routes(ORIGIN, DESTINATION)


@pytest.mark.parametrize(
    "payload",
    [
        {"code": "Ok", "routes": "not-a-list"},
        {"code": "Ok", "routes": [route_payload(distance=0)]},
        {"code": "Ok", "routes": [route_payload(duration=float("nan"))]},
        {
            "code": "Ok",
            "routes": [
                {
                    "distance": 1000,
                    "duration": 60,
                    "geometry": {"type": "Point", "coordinates": [1, 2]},
                }
            ],
        },
        {
            "code": "Ok",
            "routes": [
                {
                    "distance": 1000,
                    "duration": 60,
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [[1, 2]],
                    },
                }
            ],
        },
    ],
)
def test_rejects_invalid_route_responses(payload: dict) -> None:
    with patch(
        "services.routing.requests.get",
        return_value=osrm_response(payload),
    ):
        with pytest.raises(InvalidRoutingResponseError):
            get_routes(ORIGIN, DESTINATION)


def test_rejects_invalid_json() -> None:
    response = osrm_response({})
    response.json.side_effect = ValueError("invalid")
    with patch("services.routing.requests.get", return_value=response):
        with pytest.raises(InvalidRoutingResponseError):
            get_routes(ORIGIN, DESTINATION)
