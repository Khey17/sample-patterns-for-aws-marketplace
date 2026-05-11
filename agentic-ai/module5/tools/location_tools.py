# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""
module5/tools/location_tools.py
================================
Amazon Location Service tools for the geospatial intelligence domain.

Uses boto3 in live mode, falls back to mock data when
AGENT_MOCK_DOMAIN=true or when credentials are unavailable.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone

from langchain_core.tools import tool

from module5.mock.domain_mocks import (
    mock_location_geocode,
    mock_location_reverse_geocode,
    mock_location_calculate_route,
    mock_location_search_nearby,
)

def _is_mock() -> bool:
    return os.getenv("AGENT_MOCK_DOMAIN", "true").lower() == "true"


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _location_client():
    import boto3
    region = os.getenv("AWS_REGION", "us-east-1")
    return boto3.client("location", region_name=region)


@tool
def location_geocode(address: str, index_name: str = "devops-place-index") -> str:
    """Geocode an address to coordinates using Amazon Location Service.

    Args:
        address: Street address or place name to geocode.
        index_name: Amazon Location place index name (default: devops-place-index).

    Returns:
        JSON string with Output_Envelope containing coordinates and place details.
    """
    index_name = os.getenv("AGENT_LOCATION_INDEX_NAME", index_name)
    if _is_mock():
        return json.dumps(mock_location_geocode(address=address, index_name=index_name), indent=2)
    try:
        client = _location_client()
        response = client.search_place_index_for_text(
            IndexName=index_name, Text=address, MaxResults=1,
        )
        results = response.get("Results", [])
        result = results[0] if results else {}
        return json.dumps(
            {"tool": "location_geocode", "timestamp": _timestamp(), "mock_mode": False,
             "data": {"query": address, "index_name": index_name, "result": result}},
            indent=2, default=str,
        )
    except (ImportError, KeyError):
        return json.dumps(mock_location_geocode(address=address, index_name=index_name), indent=2)
    except Exception as e:
        return json.dumps(
            {"tool": "location_geocode", "timestamp": _timestamp(), "mock_mode": False,
             "data": {"error": str(e)}}, indent=2,
        )


@tool
def location_reverse_geocode(
    latitude: float, longitude: float, index_name: str = "devops-place-index"
) -> str:
    """Reverse geocode coordinates to an address using Amazon Location Service.

    Args:
        latitude: Latitude of the point to reverse geocode.
        longitude: Longitude of the point to reverse geocode.
        index_name: Amazon Location place index name (default: devops-place-index).

    Returns:
        JSON string with Output_Envelope containing address and place details.
    """
    index_name = os.getenv("AGENT_LOCATION_INDEX_NAME", index_name)
    if _is_mock():
        return json.dumps(
            mock_location_reverse_geocode(latitude=latitude, longitude=longitude, index_name=index_name),
            indent=2,
        )
    try:
        client = _location_client()
        response = client.search_place_index_for_position(
            IndexName=index_name, Position=[longitude, latitude], MaxResults=1,
        )
        results = response.get("Results", [])
        result = results[0] if results else {}
        return json.dumps(
            {"tool": "location_reverse_geocode", "timestamp": _timestamp(), "mock_mode": False,
             "data": {"query": {"latitude": latitude, "longitude": longitude},
                      "index_name": index_name, "result": result}},
            indent=2, default=str,
        )
    except (ImportError, KeyError):
        return json.dumps(
            mock_location_reverse_geocode(latitude=latitude, longitude=longitude, index_name=index_name),
            indent=2,
        )
    except Exception as e:
        return json.dumps(
            {"tool": "location_reverse_geocode", "timestamp": _timestamp(), "mock_mode": False,
             "data": {"error": str(e)}}, indent=2,
        )


@tool
def location_calculate_route(origin: str, destination: str, travel_mode: str = "Car") -> str:
    """Calculate a route between two coordinate pairs using Amazon Location Service.

    Args:
        origin: Comma-separated "longitude,latitude" string for the start point.
        destination: Comma-separated "longitude,latitude" string for the end point.
        travel_mode: Travel mode — "Car", "Truck", or "Walking" (default: Car).

    Returns:
        JSON string with Output_Envelope containing route summary and steps.
    """
    calculator_name = os.getenv("AGENT_LOCATION_ROUTE_CALCULATOR", "devops-route-calculator")
    try:
        origin_coords = [float(x.strip()) for x in origin.split(",")]
        destination_coords = [float(x.strip()) for x in destination.split(",")]
    except (ValueError, AttributeError):
        return json.dumps(
            {"tool": "location_calculate_route", "timestamp": _timestamp(), "mock_mode": False,
             "data": {"error": f"Invalid coordinate format. Expected 'longitude,latitude', got origin={origin!r}, destination={destination!r}"}},
            indent=2,
        )

    if _is_mock():
        return json.dumps(
            mock_location_calculate_route(origin=origin_coords, destination=destination_coords, travel_mode=travel_mode),
            indent=2,
        )
    try:
        client = _location_client()
        response = client.calculate_route(
            CalculatorName=calculator_name,
            DeparturePosition=origin_coords,
            DestinationPosition=destination_coords,
            TravelMode=travel_mode,
        )
        return json.dumps(
            {"tool": "location_calculate_route", "timestamp": _timestamp(), "mock_mode": False,
             "data": {"origin": origin_coords, "destination": destination_coords,
                      "travel_mode": travel_mode, "summary": response.get("Summary", {}),
                      "legs": response.get("Legs", [])}},
            indent=2, default=str,
        )
    except (ImportError, KeyError):
        return json.dumps(
            mock_location_calculate_route(origin=origin_coords, destination=destination_coords, travel_mode=travel_mode),
            indent=2,
        )
    except Exception as e:
        return json.dumps(
            {"tool": "location_calculate_route", "timestamp": _timestamp(), "mock_mode": False,
             "data": {"error": str(e)}}, indent=2,
        )


@tool
def location_search_nearby(
    latitude: float, longitude: float, categories: str = "Coffee Shop", max_results: int = 3,
) -> str:
    """Search for nearby places by category using Amazon Location Service.

    Args:
        latitude: Latitude of the center point.
        longitude: Longitude of the center point.
        categories: Comma-separated category string (e.g. "Coffee Shop,Restaurant").
        max_results: Maximum number of results to return (default: 3).

    Returns:
        JSON string with Output_Envelope containing nearby place results.
    """
    index_name = os.getenv("AGENT_LOCATION_INDEX_NAME", "devops-place-index")
    category_list = [c.strip() for c in categories.split(",")]

    if _is_mock():
        return json.dumps(
            mock_location_search_nearby(latitude=latitude, longitude=longitude,
                                        categories=category_list, max_results=max_results),
            indent=2,
        )
    try:
        client = _location_client()
        response = client.search_place_index_for_text(
            IndexName=index_name, Text=categories,
            BiasPosition=[longitude, latitude], MaxResults=max_results,
        )
        results = response.get("Results", [])
        return json.dumps(
            {"tool": "location_search_nearby", "timestamp": _timestamp(), "mock_mode": False,
             "data": {"center": {"latitude": latitude, "longitude": longitude},
                      "categories": category_list, "results": results}},
            indent=2, default=str,
        )
    except (ImportError, KeyError):
        return json.dumps(
            mock_location_search_nearby(latitude=latitude, longitude=longitude,
                                        categories=category_list, max_results=max_results),
            indent=2,
        )
    except Exception as e:
        return json.dumps(
            {"tool": "location_search_nearby", "timestamp": _timestamp(), "mock_mode": False,
             "data": {"error": str(e)}}, indent=2,
        )
