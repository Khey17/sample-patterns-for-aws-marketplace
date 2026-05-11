# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""
module5/tools/mapbox_tools.py
================================
Mapbox REST API tools for the geospatial intelligence domain.

Uses the requests library in live mode, falls back to mock data when
AGENT_MOCK_DOMAIN=true or when the library / credentials are unavailable.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from urllib.parse import quote

from langchain_core.tools import tool

from module5.mock.domain_mocks import (
    mock_mapbox_forward_geocode,
    mock_mapbox_get_directions,
    mock_mapbox_isochrone,
    mock_mapbox_poi_search,
)

def _is_mock() -> bool:
    return os.getenv("AGENT_MOCK_DOMAIN", "true").lower() == "true"


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


@tool
def mapbox_forward_geocode(address: str, country: str = "us") -> str:
    """Forward geocode an address using Mapbox Geocoding API.

    Args:
        address: Street address or place name to geocode.
        country: ISO 3166-1 alpha-2 country code to filter results (default: us).

    Returns:
        JSON string with Output_Envelope containing coordinates and place details.
    """
    if _is_mock():
        return json.dumps(mock_mapbox_forward_geocode(address=address, country=country), indent=2)
    try:
        import requests

        encoded_address = quote(address)
        token = os.environ["MAPBOX_ACCESS_TOKEN"]
        response = requests.get(
            f"https://api.mapbox.com/geocoding/v5/mapbox.places/{encoded_address}.json",
            params={"access_token": token, "country": country, "limit": 1},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        return json.dumps(
            {
                "tool": "mapbox_forward_geocode",
                "timestamp": _timestamp(),
                "mock_mode": False,
                "data": {
                    "query": address,
                    "country": country,
                    "features": data.get("features", []),
                    "attribution": data.get("attribution", "Mapbox"),
                },
            },
            indent=2,
        )
    except (ImportError, KeyError):
        return json.dumps(mock_mapbox_forward_geocode(address=address, country=country), indent=2)
    except Exception as e:
        return json.dumps(
            {
                "tool": "mapbox_forward_geocode",
                "timestamp": _timestamp(),
                "mock_mode": False,
                "data": {"error": str(e)},
            },
            indent=2,
        )


@tool
def mapbox_get_directions(
    origin: str, destination: str, profile: str = "mapbox/driving"
) -> str:
    """Get driving/walking directions using Mapbox Directions API.

    Args:
        origin: Comma-separated "longitude,latitude" string for the start point.
        destination: Comma-separated "longitude,latitude" string for the end point.
        profile: Routing profile — "mapbox/driving", "mapbox/walking", or "mapbox/cycling"
                 (default: mapbox/driving).

    Returns:
        JSON string with Output_Envelope containing route with distance, duration, and steps.
    """
    if _is_mock():
        return json.dumps(
            mock_mapbox_get_directions(
                origin=origin, destination=destination, profile=profile
            ),
            indent=2,
        )
    try:
        import requests

        token = os.environ["MAPBOX_ACCESS_TOKEN"]
        response = requests.get(
            f"https://api.mapbox.com/directions/v5/{profile}/{origin};{destination}",
            params={"access_token": token, "steps": "true", "geometries": "geojson"},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        return json.dumps(
            {
                "tool": "mapbox_get_directions",
                "timestamp": _timestamp(),
                "mock_mode": False,
                "data": {
                    "profile": profile,
                    "origin": origin,
                    "destination": destination,
                    "routes": data.get("routes", []),
                    "waypoints": data.get("waypoints", []),
                    "code": data.get("code", ""),
                },
            },
            indent=2,
        )
    except (ImportError, KeyError):
        return json.dumps(
            mock_mapbox_get_directions(
                origin=origin, destination=destination, profile=profile
            ),
            indent=2,
        )
    except Exception as e:
        return json.dumps(
            {
                "tool": "mapbox_get_directions",
                "timestamp": _timestamp(),
                "mock_mode": False,
                "data": {"error": str(e)},
            },
            indent=2,
        )


@tool
def mapbox_isochrone(
    longitude: float,
    latitude: float,
    contours_minutes: str = "5,10,15",
    profile: str = "mapbox/driving",
) -> str:
    """Generate isochrone polygons (reachable areas) using Mapbox Isochrone API.

    Args:
        longitude: Longitude of the center point.
        latitude: Latitude of the center point.
        contours_minutes: Comma-separated string of travel time contours in minutes
                          (default: "5,10,15").
        profile: Routing profile — "mapbox/driving", "mapbox/walking", or "mapbox/cycling"
                 (default: mapbox/driving).

    Returns:
        JSON string with Output_Envelope containing isochrone polygon features.
    """
    contour_list = [int(x.strip()) for x in contours_minutes.split(",")]

    if _is_mock():
        return json.dumps(
            mock_mapbox_isochrone(
                longitude=longitude,
                latitude=latitude,
                contours_minutes=contour_list,
                profile=profile,
            ),
            indent=2,
        )
    try:
        import requests

        token = os.environ["MAPBOX_ACCESS_TOKEN"]
        response = requests.get(
            f"https://api.mapbox.com/isochrone/v1/{profile}/{longitude},{latitude}",
            params={"contours_minutes": contours_minutes, "access_token": token},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        return json.dumps(
            {
                "tool": "mapbox_isochrone",
                "timestamp": _timestamp(),
                "mock_mode": False,
                "data": {
                    "center": [longitude, latitude],
                    "profile": profile,
                    "contours_minutes": contour_list,
                    "type": data.get("type", "FeatureCollection"),
                    "features": data.get("features", []),
                },
            },
            indent=2,
        )
    except (ImportError, KeyError):
        return json.dumps(
            mock_mapbox_isochrone(
                longitude=longitude,
                latitude=latitude,
                contours_minutes=contour_list,
                profile=profile,
            ),
            indent=2,
        )
    except Exception as e:
        return json.dumps(
            {
                "tool": "mapbox_isochrone",
                "timestamp": _timestamp(),
                "mock_mode": False,
                "data": {"error": str(e)},
            },
            indent=2,
        )


@tool
def mapbox_poi_search(
    query: str, longitude: float, latitude: float, radius_km: float = 1.0
) -> str:
    """Search for points of interest near a location using Mapbox Search API.

    Args:
        query: Search term for the type of POI (e.g. "coffee shop", "hospital").
        longitude: Longitude of the center point for proximity search.
        latitude: Latitude of the center point for proximity search.
        radius_km: Search radius in kilometers (default: 1.0).

    Returns:
        JSON string with Output_Envelope containing POI features with coordinates.
    """
    if _is_mock():
        return json.dumps(
            mock_mapbox_poi_search(
                query=query,
                longitude=longitude,
                latitude=latitude,
                radius_km=radius_km,
            ),
            indent=2,
        )
    try:
        import requests

        token = os.environ["MAPBOX_ACCESS_TOKEN"]
        encoded_query = quote(query)
        response = requests.get(
            f"https://api.mapbox.com/geocoding/v5/mapbox.places/{encoded_query}.json",
            params={
                "proximity": f"{longitude},{latitude}",
                "access_token": token,
                "limit": 5,
                "types": "poi",
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        return json.dumps(
            {
                "tool": "mapbox_poi_search",
                "timestamp": _timestamp(),
                "mock_mode": False,
                "data": {
                    "query": query,
                    "center": [longitude, latitude],
                    "radius_km": radius_km,
                    "features": data.get("features", []),
                },
            },
            indent=2,
        )
    except (ImportError, KeyError):
        return json.dumps(
            mock_mapbox_poi_search(
                query=query,
                longitude=longitude,
                latitude=latitude,
                radius_km=radius_km,
            ),
            indent=2,
        )
    except Exception as e:
        return json.dumps(
            {
                "tool": "mapbox_poi_search",
                "timestamp": _timestamp(),
                "mock_mode": False,
                "data": {"error": str(e)},
            },
            indent=2,
        )
