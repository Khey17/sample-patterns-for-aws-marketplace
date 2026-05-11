# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""
module5/tools/__init__.py
==========================
Shared tool registry for all Module 5 domain agents.

ALL_TOOLS maps tool name strings to BaseTool instances and is passed to
DomainAdapter so ToolScoper can select the right subset per domain.
"""

from __future__ import annotations

from langchain_core.tools import BaseTool

from module5.tools.algolia_tools import algolia_semantic_search
from module5.tools.personalize_tools import personalize_get_recommendations
from module5.tools.lex_tools import lex_classify_intent
from module5.tools.connect_tools import connect_escalate_to_human
from module5.tools.location_tools import (
    location_geocode,
    location_reverse_geocode,
    location_calculate_route,
    location_search_nearby,
)
from module5.tools.mapbox_tools import (
    mapbox_forward_geocode,
    mapbox_get_directions,
    mapbox_isochrone,
    mapbox_poi_search,
)
from module5.tools.deepgram_tools import deepgram_transcribe, deepgram_synthesize
from module5.tools.transcribe_tools import transcribe_audio
from module5.tools.polly_tools import polly_synthesize

ALL_TOOLS: dict[str, BaseTool] = {
    # Customer engagement
    "algolia_semantic_search": algolia_semantic_search,
    "personalize_get_recommendations": personalize_get_recommendations,
    "lex_classify_intent": lex_classify_intent,
    "connect_escalate_to_human": connect_escalate_to_human,
    # Geospatial intelligence
    "location_geocode": location_geocode,
    "location_reverse_geocode": location_reverse_geocode,
    "location_calculate_route": location_calculate_route,
    "location_search_nearby": location_search_nearby,
    "mapbox_forward_geocode": mapbox_forward_geocode,
    "mapbox_get_directions": mapbox_get_directions,
    "mapbox_isochrone": mapbox_isochrone,
    "mapbox_poi_search": mapbox_poi_search,
    # Voice interaction
    "deepgram_transcribe": deepgram_transcribe,
    "deepgram_synthesize": deepgram_synthesize,
    "transcribe_audio": transcribe_audio,
    "polly_synthesize": polly_synthesize,
}

__all__ = ["ALL_TOOLS"]
