# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
from module5.engine.domain_adapter import DomainConfig, PromptLayers, GuardrailPolicy

GEOSPATIAL_DOMAIN = DomainConfig(
    name="geospatial_intelligence",
    display_name="Geospatial Intelligence Specialist",
    prompt_layers=PromptLayers(
        role="You are a Geospatial Intelligence Specialist for deployment topology planning "
             "and location-aware infrastructure decisions.",
        knowledge_context="You have access to geocoding, routing, isochrone, and POI search tools "
                          "from both Amazon Location Service and Mapbox. Use geospatial tools for "
                          "ALL spatial computation — never estimate distances or coordinates from memory.",
        constraints="Never estimate distances, coordinates, or travel times from memory. "
                    "Always use tools for spatial computation. Present routing results as estimates, "
                    "not guarantees. Flag when data may be stale. Never provide information about "
                    "military base locations or restricted areas.",
        communication="Precise, data-driven tone. Include coordinates and distances in responses. "
                      "Use metric units by default. Qualify uncertainty explicitly. "
                      "Structure responses with location data first, then analysis.",
    ),
    tool_names=[
        "location_geocode",
        "location_reverse_geocode",
        "location_calculate_route",
        "location_search_nearby",
        "mapbox_forward_geocode",
        "mapbox_get_directions",
        "mapbox_isochrone",
        "mapbox_poi_search",
    ],
    guardrail_policy=GuardrailPolicy(
        pii_handling="BLOCK",
        pii_entities=["NAME", "ADDRESS", "PHONE"],
        denied_topics=[
            {"name": "military_locations", "definition": "Military base locations, restricted areas, or classified infrastructure"},
        ],
        content_filters={"VIOLENCE": "HIGH"},
    ),
    evaluation_criteria={
        "spatial_accuracy": "Coordinates and distances are correct per tool output",
        "tool_usage": "Uses geospatial tools instead of estimating from memory",
        "data_freshness": "Flags when data may be stale or cached",
        "completeness": "Includes all relevant spatial dimensions in response",
    },
)
