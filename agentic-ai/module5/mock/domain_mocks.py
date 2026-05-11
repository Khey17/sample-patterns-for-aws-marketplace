# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""
module5/mock/domain_mocks.py
============================
Mock responses for all Module 5 domain tool files.

Provides realistic, deterministic mock data for all 16 tool functions
across the three domain configurations (customer engagement, geospatial
intelligence, voice interaction). Used when AGENT_MOCK_DOMAIN=true.

Each mock function returns a dict conforming to the Output_Envelope schema:
    {
        "tool": "<tool_name>",
        "timestamp": "<ISO timestamp>",
        "mock_mode": True,
        "data": { ... }
    }
"""

from __future__ import annotations

from datetime import datetime, timezone


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Customer Engagement Domain Mocks
# ---------------------------------------------------------------------------


def mock_algolia_semantic_search(
    query: str = "monitoring dashboard",
    index_name: str = "devops-companion-catalog",
    **kwargs,
) -> dict:
    """Mock Algolia AI semantic search — returns 3 ranked product hits."""
    return {
        "tool": "algolia_semantic_search",
        "timestamp": _timestamp(),
        "mock_mode": True,
        "data": {
            "query": query,
            "index": index_name,
            "nb_hits": 3,
            "hits": [
                {
                    "objectID": "prod-001",
                    "name": "DevOps Companion Pro",
                    "description": (
                        "Full-stack observability platform with AI-powered anomaly detection, "
                        "real-time dashboards, and automated incident response workflows."
                    ),
                    "price": 299.00,
                    "currency": "USD",
                    "category": "Observability",
                    "rating": 4.8,
                    "_score": 0.97,
                },
                {
                    "objectID": "prod-042",
                    "name": "CloudWatch Insights Accelerator",
                    "description": (
                        "Pre-built CloudWatch dashboards and metric aggregation rules "
                        "for ECS, RDS, and Lambda workloads. Deploys in under 5 minutes."
                    ),
                    "price": 49.00,
                    "currency": "USD",
                    "category": "Monitoring",
                    "rating": 4.5,
                    "_score": 0.91,
                },
                {
                    "objectID": "prod-117",
                    "name": "Incident Response Playbook Suite",
                    "description": (
                        "Curated runbooks and automated escalation workflows for common "
                        "AWS infrastructure incidents. Integrates with PagerDuty and Slack."
                    ),
                    "price": 129.00,
                    "currency": "USD",
                    "category": "Incident Management",
                    "rating": 4.6,
                    "_score": 0.84,
                },
            ],
        },
    }


def mock_personalize_get_recommendations(
    user_id: str = "user-8472",
    num_results: int = 5,
    **kwargs,
) -> dict:
    """Mock Amazon Personalize recommendations — returns 5 item IDs with scores."""
    items = [
        {"item_id": "prod-001", "score": 0.94, "reason": "Matches past purchases in Observability"},
        {"item_id": "prod-088", "score": 0.87, "reason": "Trending in your industry segment"},
        {"item_id": "prod-042", "score": 0.81, "reason": "Frequently bought together with prod-001"},
        {"item_id": "prod-203", "score": 0.76, "reason": "Based on browsing history"},
        {"item_id": "prod-117", "score": 0.71, "reason": "Popular with similar users"},
    ]
    return {
        "tool": "personalize_get_recommendations",
        "timestamp": _timestamp(),
        "mock_mode": True,
        "data": {
            "user_id": user_id,
            "recommendation_id": "rec-20250714-8472",
            "items": items[:num_results],
        },
    }


def mock_lex_classify_intent(
    text: str = "I need help with my subscription",
    bot_id: str = "DEVOPS_BOT",
    bot_alias_id: str = "PROD",
    locale_id: str = "en_US",
    **kwargs,
) -> dict:
    """Mock Amazon Lex V2 intent classification — returns intent, confidence, slots."""
    return {
        "tool": "lex_classify_intent",
        "timestamp": _timestamp(),
        "mock_mode": True,
        "data": {
            "input_text": text,
            "bot_id": bot_id,
            "locale_id": locale_id,
            "session_id": "sess-mock-001",
            "intent": {
                "name": "ManageSubscription",
                "confidence_score": 0.93,
                "state": "ReadyForFulfillment",
            },
            "slots": {
                "SubscriptionAction": {
                    "value": {"interpreted_value": "upgrade", "original_value": "help"},
                    "shape": "Scalar",
                },
                "PlanTier": {
                    "value": None,
                    "shape": "Scalar",
                },
            },
            "sentiment": {
                "label": "NEUTRAL",
                "scores": {"positive": 0.31, "negative": 0.08, "neutral": 0.61},
            },
        },
    }


def mock_connect_escalate_to_human(
    reason: str = "Customer requesting billing dispute resolution",
    customer_id: str = "cust-5521",
    priority: str = "NORMAL",
    **kwargs,
) -> dict:
    """Mock Amazon Connect escalation — returns ticket with queue and wait time."""
    return {
        "tool": "connect_escalate_to_human",
        "timestamp": _timestamp(),
        "mock_mode": True,
        "data": {
            "ticket_id": "TKT-20250714-5521",
            "customer_id": customer_id,
            "status": "QUEUED",
            "priority": priority,
            "reason": reason,
            "queue": "billing-support-tier2",
            "estimated_wait_minutes": 4,
            "contact_id": "contact-mock-abc123",
            "agent_assigned": None,
            "channel": "CHAT",
        },
    }


# ---------------------------------------------------------------------------
# Geospatial Intelligence Domain Mocks — Amazon Location Service
# ---------------------------------------------------------------------------


def mock_location_geocode(
    address: str = "410 Terry Ave N, Seattle, WA 98109",
    index_name: str = "devops-place-index",
    **kwargs,
) -> dict:
    """Mock Amazon Location Service geocode — returns lat/lng for an address."""
    return {
        "tool": "location_geocode",
        "timestamp": _timestamp(),
        "mock_mode": True,
        "data": {
            "query": address,
            "index_name": index_name,
            "result": {
                "place": {
                    "label": "410 Terry Ave N, Seattle, WA 98109, United States",
                    "address_number": "410",
                    "street": "Terry Ave N",
                    "municipality": "Seattle",
                    "region": "Washington",
                    "postal_code": "98109",
                    "country": "USA",
                },
                "geometry": {
                    "point": [-122.3367, 47.6205],
                },
                "relevance": 0.99,
            },
        },
    }


def mock_location_reverse_geocode(
    latitude: float = 47.6205,
    longitude: float = -122.3367,
    index_name: str = "devops-place-index",
    **kwargs,
) -> dict:
    """Mock Amazon Location Service reverse geocode — returns address from coordinates."""
    return {
        "tool": "location_reverse_geocode",
        "timestamp": _timestamp(),
        "mock_mode": True,
        "data": {
            "query": {"latitude": latitude, "longitude": longitude},
            "index_name": index_name,
            "result": {
                "place": {
                    "label": "410 Terry Ave N, Seattle, WA 98109, United States",
                    "address_number": "410",
                    "street": "Terry Ave N",
                    "municipality": "Seattle",
                    "sub_region": "King County",
                    "region": "Washington",
                    "postal_code": "98109",
                    "country": "USA",
                },
                "geometry": {
                    "point": [longitude, latitude],
                },
            },
        },
    }


def mock_location_calculate_route(
    origin: list = None,
    destination: list = None,
    travel_mode: str = "Car",
    **kwargs,
) -> dict:
    """Mock Amazon Location Service route calculation — returns distance, duration, steps."""
    origin = origin or [-122.3367, 47.6205]
    destination = destination or [-122.3321, 47.6062]
    return {
        "tool": "location_calculate_route",
        "timestamp": _timestamp(),
        "mock_mode": True,
        "data": {
            "origin": origin,
            "destination": destination,
            "travel_mode": travel_mode,
            "summary": {
                "distance_km": 2.4,
                "duration_minutes": 8,
                "data_source": "Esri",
            },
            "legs": [
                {
                    "distance_km": 2.4,
                    "duration_minutes": 8,
                    "steps": [
                        {
                            "distance_km": 0.3,
                            "duration_minutes": 1,
                            "geometry": {"line_string": [origin, [-122.3367, 47.6180]]},
                            "start_position": origin,
                            "end_position": [-122.3367, 47.6180],
                        },
                        {
                            "distance_km": 1.8,
                            "duration_minutes": 5,
                            "geometry": {"line_string": [[-122.3367, 47.6180], [-122.3340, 47.6100]]},
                            "start_position": [-122.3367, 47.6180],
                            "end_position": [-122.3340, 47.6100],
                        },
                        {
                            "distance_km": 0.3,
                            "duration_minutes": 2,
                            "geometry": {"line_string": [[-122.3340, 47.6100], destination]},
                            "start_position": [-122.3340, 47.6100],
                            "end_position": destination,
                        },
                    ],
                }
            ],
        },
    }


def mock_location_search_nearby(
    latitude: float = 47.6205,
    longitude: float = -122.3367,
    categories: list = None,
    max_results: int = 3,
    **kwargs,
) -> dict:
    """Mock Amazon Location Service nearby search — returns 3 nearby places."""
    categories = categories or ["Coffee Shop"]
    return {
        "tool": "location_search_nearby",
        "timestamp": _timestamp(),
        "mock_mode": True,
        "data": {
            "center": {"latitude": latitude, "longitude": longitude},
            "categories": categories,
            "results": [
                {
                    "place_id": "place-001",
                    "name": "Starbucks Reserve Roastery",
                    "categories": ["Coffee Shop"],
                    "address": "1124 Pike St, Seattle, WA 98101",
                    "geometry": {"point": [-122.3330, 47.6138]},
                    "distance_meters": 780,
                },
                {
                    "place_id": "place-002",
                    "name": "Caffe Vita",
                    "categories": ["Coffee Shop"],
                    "address": "813 5th Ave N, Seattle, WA 98109",
                    "geometry": {"point": [-122.3420, 47.6240]},
                    "distance_meters": 1020,
                },
                {
                    "place_id": "place-003",
                    "name": "Lighthouse Coffee",
                    "categories": ["Coffee Shop"],
                    "address": "400 Westlake Ave N, Seattle, WA 98109",
                    "geometry": {"point": [-122.3380, 47.6215]},
                    "distance_meters": 1350,
                },
            ][:max_results],
        },
    }


# ---------------------------------------------------------------------------
# Geospatial Intelligence Domain Mocks — Mapbox
# ---------------------------------------------------------------------------


def mock_mapbox_forward_geocode(
    address: str = "410 Terry Ave N, Seattle, WA",
    country: str = "us",
    **kwargs,
) -> dict:
    """Mock Mapbox forward geocode — returns coordinates with place_name."""
    return {
        "tool": "mapbox_forward_geocode",
        "timestamp": _timestamp(),
        "mock_mode": True,
        "data": {
            "query": address,
            "country": country,
            "features": [
                {
                    "id": "address.8675309",
                    "type": "Feature",
                    "place_name": "410 Terry Avenue North, Seattle, Washington 98109, United States",
                    "relevance": 0.99,
                    "geometry": {
                        "type": "Point",
                        "coordinates": [-122.3367, 47.6205],
                    },
                    "properties": {
                        "accuracy": "rooftop",
                    },
                    "context": [
                        {"id": "postcode.123", "text": "98109"},
                        {"id": "place.456", "text": "Seattle"},
                        {"id": "region.789", "text": "Washington"},
                        {"id": "country.012", "text": "United States"},
                    ],
                }
            ],
            "attribution": "Mapbox",
        },
    }


def mock_mapbox_get_directions(
    origin: list = None,
    destination: list = None,
    profile: str = "mapbox/driving",
    **kwargs,
) -> dict:
    """Mock Mapbox directions — returns route with distance, duration, steps."""
    origin = origin or [-122.3367, 47.6205]
    destination = destination or [-122.3321, 47.6062]
    return {
        "tool": "mapbox_get_directions",
        "timestamp": _timestamp(),
        "mock_mode": True,
        "data": {
            "profile": profile,
            "origin": origin,
            "destination": destination,
            "routes": [
                {
                    "distance": 2410,
                    "duration": 487,
                    "weight": 512.3,
                    "geometry": "mock_encoded_polyline_string",
                    "legs": [
                        {
                            "distance": 2410,
                            "duration": 487,
                            "steps": [
                                {
                                    "distance": 310,
                                    "duration": 62,
                                    "maneuver": {
                                        "instruction": "Head south on Terry Ave N",
                                        "type": "depart",
                                        "bearing_after": 180,
                                    },
                                },
                                {
                                    "distance": 1800,
                                    "duration": 360,
                                    "maneuver": {
                                        "instruction": "Turn left onto Denny Way",
                                        "type": "turn",
                                        "modifier": "left",
                                    },
                                },
                                {
                                    "distance": 300,
                                    "duration": 65,
                                    "maneuver": {
                                        "instruction": "Arrive at destination",
                                        "type": "arrive",
                                    },
                                },
                            ],
                        }
                    ],
                }
            ],
            "waypoints": [
                {"name": "Terry Ave N", "location": origin},
                {"name": "Destination", "location": destination},
            ],
            "code": "Ok",
        },
    }


def mock_mapbox_isochrone(
    longitude: float = -122.3367,
    latitude: float = 47.6205,
    contours_minutes: list = None,
    profile: str = "mapbox/driving",
    **kwargs,
) -> dict:
    """Mock Mapbox isochrone — returns isochrone polygon summary."""
    contours_minutes = contours_minutes or [5, 10, 15]
    features = []
    for minutes in contours_minutes:
        features.append(
            {
                "type": "Feature",
                "properties": {
                    "contour": minutes,
                    "color": "#3bb2d0" if minutes == min(contours_minutes) else "#223b53",
                    "opacity": 0.3,
                    "fill": "#3bb2d0",
                    "fill-opacity": 0.3,
                    "metric": "time",
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [longitude - 0.01 * minutes, latitude - 0.008 * minutes],
                            [longitude + 0.01 * minutes, latitude - 0.008 * minutes],
                            [longitude + 0.01 * minutes, latitude + 0.008 * minutes],
                            [longitude - 0.01 * minutes, latitude + 0.008 * minutes],
                            [longitude - 0.01 * minutes, latitude - 0.008 * minutes],
                        ]
                    ],
                },
            }
        )
    return {
        "tool": "mapbox_isochrone",
        "timestamp": _timestamp(),
        "mock_mode": True,
        "data": {
            "center": [longitude, latitude],
            "profile": profile,
            "contours_minutes": contours_minutes,
            "type": "FeatureCollection",
            "features": features,
            "summary": {
                f"{m}_min_radius_km": round(m * 0.4, 1) for m in contours_minutes
            },
        },
    }


def mock_mapbox_poi_search(
    query: str = "coffee shop",
    longitude: float = -122.3367,
    latitude: float = 47.6205,
    radius_km: float = 1.0,
    **kwargs,
) -> dict:
    """Mock Mapbox POI search — returns 3 POI results."""
    return {
        "tool": "mapbox_poi_search",
        "timestamp": _timestamp(),
        "mock_mode": True,
        "data": {
            "query": query,
            "center": [longitude, latitude],
            "radius_km": radius_km,
            "features": [
                {
                    "id": "poi.111",
                    "type": "Feature",
                    "place_name": "Starbucks Reserve Roastery, 1124 Pike St, Seattle, WA 98101",
                    "relevance": 0.98,
                    "geometry": {"type": "Point", "coordinates": [-122.3330, 47.6138]},
                    "properties": {
                        "category": "coffee",
                        "maki": "cafe",
                        "landmark": True,
                        "address": "1124 Pike St",
                    },
                    "distance_km": 0.78,
                },
                {
                    "id": "poi.222",
                    "type": "Feature",
                    "place_name": "Caffe Vita, 813 5th Ave N, Seattle, WA 98109",
                    "relevance": 0.91,
                    "geometry": {"type": "Point", "coordinates": [-122.3420, 47.6240]},
                    "properties": {
                        "category": "coffee",
                        "maki": "cafe",
                        "landmark": False,
                        "address": "813 5th Ave N",
                    },
                    "distance_km": 0.95,
                },
                {
                    "id": "poi.333",
                    "type": "Feature",
                    "place_name": "Lighthouse Coffee, 400 Westlake Ave N, Seattle, WA 98109",
                    "relevance": 0.85,
                    "geometry": {"type": "Point", "coordinates": [-122.3380, 47.6215]},
                    "properties": {
                        "category": "coffee",
                        "maki": "cafe",
                        "landmark": False,
                        "address": "400 Westlake Ave N",
                    },
                    "distance_km": 0.99,
                },
            ],
        },
    }


# ---------------------------------------------------------------------------
# Voice Interaction Domain Mocks — Deepgram
# ---------------------------------------------------------------------------


def mock_deepgram_transcribe(
    audio_url: str = "s3://devops-companion-audio/session-001.wav",
    model: str = "nova-3",
    language: str = "en-US",
    **kwargs,
) -> dict:
    """Mock Deepgram transcription — returns transcript with confidence and words."""
    return {
        "tool": "deepgram_transcribe",
        "timestamp": _timestamp(),
        "mock_mode": True,
        "data": {
            "audio_url": audio_url,
            "model": model,
            "language": language,
            "transcript": (
                "I need to check the status of my ECS cluster in us-east-1 "
                "and find out why the notification service keeps restarting."
            ),
            "confidence": 0.97,
            "duration_seconds": 6.4,
            "words": [
                {"word": "I", "start": 0.00, "end": 0.10, "confidence": 0.99},
                {"word": "need", "start": 0.10, "end": 0.28, "confidence": 0.99},
                {"word": "to", "start": 0.28, "end": 0.38, "confidence": 0.98},
                {"word": "check", "start": 0.38, "end": 0.62, "confidence": 0.97},
                {"word": "the", "start": 0.62, "end": 0.72, "confidence": 0.99},
                {"word": "status", "start": 0.72, "end": 1.05, "confidence": 0.96},
                {"word": "of", "start": 1.05, "end": 1.15, "confidence": 0.99},
                {"word": "my", "start": 1.15, "end": 1.28, "confidence": 0.98},
                {"word": "ECS", "start": 1.28, "end": 1.60, "confidence": 0.94},
                {"word": "cluster", "start": 1.60, "end": 1.95, "confidence": 0.97},
            ],
            "paragraphs": [
                {
                    "transcript": (
                        "I need to check the status of my ECS cluster in us-east-1 "
                        "and find out why the notification service keeps restarting."
                    ),
                    "start": 0.00,
                    "end": 6.40,
                    "num_words": 22,
                }
            ],
            "metadata": {
                "request_id": "dg-req-mock-001",
                "model_info": {"name": model, "version": "2025-01-15.0"},
            },
        },
    }


def mock_deepgram_synthesize(
    text: str = "Your ECS cluster is healthy. The notification service has restarted 3 times.",
    voice: str = "aura-asteria-en",
    model: str = "aura-2",
    **kwargs,
) -> dict:
    """Mock Deepgram TTS synthesis — returns audio_url, duration, format."""
    return {
        "tool": "deepgram_synthesize",
        "timestamp": _timestamp(),
        "mock_mode": True,
        "data": {
            "input_text": text,
            "voice": voice,
            "model": model,
            "audio_url": "s3://devops-companion-audio/tts-output-mock-001.mp3",
            "duration_seconds": round(len(text.split()) * 0.35, 1),
            "format": "mp3",
            "sample_rate": 24000,
            "character_count": len(text),
            "metadata": {
                "request_id": "dg-tts-mock-001",
                "model_info": {"name": model, "version": "2025-01-15.0"},
            },
        },
    }


# ---------------------------------------------------------------------------
# Voice Interaction Domain Mocks — Amazon Transcribe
# ---------------------------------------------------------------------------


def mock_transcribe_audio(
    audio_s3_uri: str = "s3://devops-companion-audio/session-001.wav",
    language_code: str = "en-US",
    job_name: str = "transcribe-job-mock-001",
    **kwargs,
) -> dict:
    """Mock Amazon Transcribe — returns transcript, confidence, job_id."""
    return {
        "tool": "transcribe_audio",
        "timestamp": _timestamp(),
        "mock_mode": True,
        "data": {
            "job_name": job_name,
            "job_id": "transcribe-job-mock-001",
            "status": "COMPLETED",
            "language_code": language_code,
            "audio_s3_uri": audio_s3_uri,
            "transcript": (
                "I need to check the status of my ECS cluster in us-east-1 "
                "and find out why the notification service keeps restarting."
            ),
            "confidence": 0.95,
            "items": [
                {
                    "type": "pronunciation",
                    "content": "I",
                    "start_time": "0.0",
                    "end_time": "0.1",
                    "confidence": "0.99",
                },
                {
                    "type": "pronunciation",
                    "content": "need",
                    "start_time": "0.1",
                    "end_time": "0.28",
                    "confidence": "0.99",
                },
                {
                    "type": "pronunciation",
                    "content": "ECS",
                    "start_time": "1.28",
                    "end_time": "1.60",
                    "confidence": "0.93",
                },
            ],
            "output_s3_uri": "s3://devops-companion-transcripts/transcribe-job-mock-001.json",
        },
    }


# ---------------------------------------------------------------------------
# Voice Interaction Domain Mocks — Amazon Polly
# ---------------------------------------------------------------------------


def mock_polly_synthesize(
    text: str = "Your ECS cluster is healthy. The notification service has restarted 3 times.",
    voice_id: str = "Joanna",
    output_format: str = "mp3",
    engine: str = "neural",
    **kwargs,
) -> dict:
    """Mock Amazon Polly TTS synthesis — returns audio_s3_uri, duration, character_count."""
    return {
        "tool": "polly_synthesize",
        "timestamp": _timestamp(),
        "mock_mode": True,
        "data": {
            "input_text": text,
            "voice_id": voice_id,
            "output_format": output_format,
            "engine": engine,
            "audio_s3_uri": "s3://devops-companion-audio/polly-output-mock-001.mp3",
            "duration_seconds": round(len(text.split()) * 0.38, 1),
            "character_count": len(text),
            "sample_rate": "22050",
            "content_type": f"audio/{output_format}",
            "request_characters": len(text),
        },
    }


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

_MOCK_HANDLERS = {
    "algolia_semantic_search": mock_algolia_semantic_search,
    "personalize_get_recommendations": mock_personalize_get_recommendations,
    "lex_classify_intent": mock_lex_classify_intent,
    "connect_escalate_to_human": mock_connect_escalate_to_human,
    "location_geocode": mock_location_geocode,
    "location_reverse_geocode": mock_location_reverse_geocode,
    "location_calculate_route": mock_location_calculate_route,
    "location_search_nearby": mock_location_search_nearby,
    "mapbox_forward_geocode": mock_mapbox_forward_geocode,
    "mapbox_get_directions": mock_mapbox_get_directions,
    "mapbox_isochrone": mock_mapbox_isochrone,
    "mapbox_poi_search": mock_mapbox_poi_search,
    "deepgram_transcribe": mock_deepgram_transcribe,
    "deepgram_synthesize": mock_deepgram_synthesize,
    "transcribe_audio": mock_transcribe_audio,
    "polly_synthesize": mock_polly_synthesize,
}


def get_mock_response(tool_name: str, **kwargs) -> dict:
    """
    Dispatch to the correct mock function by tool name.

    Parameters
    ----------
    tool_name : str
        Name of the tool to mock (e.g. "algolia_semantic_search").
    **kwargs
        Arguments forwarded to the mock function.

    Returns
    -------
    dict
        Mock response conforming to the Output_Envelope schema.
    """
    handler = _MOCK_HANDLERS.get(tool_name)
    if handler:
        return handler(**kwargs)

    return {
        "tool": tool_name,
        "timestamp": _timestamp(),
        "mock_mode": True,
        "data": {"error": f"No mock handler registered for tool '{tool_name}'"},
    }
