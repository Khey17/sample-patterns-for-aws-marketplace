# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""
evaluation/datasets/module5_testcases.py
=========================================
Test cases for Module 5 Domain-Specific Agent evaluation.

Each test case includes:
- id: Unique identifier
- name: Human-readable test name
- category: Test category
- domain: Domain name (customer_engagement, geospatial_intelligence, voice_interaction)
- query: The user query to send to the agent
- expected_tools: List of tool names the agent should call
- evaluation_criteria: Dict of criteria keys to expected values/descriptions

Validates: Requirements 12.1, 12.3
"""

from __future__ import annotations

MODULE5_TEST_CASES = [
    # -------------------------------------------------------------------------
    # Customer Engagement domain (3 test cases)
    # Criteria: intent_accuracy, tone_appropriateness, escalation_judgment, factual_accuracy
    # -------------------------------------------------------------------------
    {
        "id": "m5-ce-001",
        "name": "Product search query",
        "category": "search",
        "domain": "customer_engagement",
        "query": (
            "I'm looking for a monitoring tool that integrates with our existing "
            "AWS infrastructure and supports custom dashboards. What do you have?"
        ),
        "expected_tools": ["algolia_semantic_search", "personalize_get_recommendations"],
        "evaluation_criteria": {
            "intent_accuracy": "Correctly identifies product discovery intent",
            "tone_appropriateness": "Warm, professional tone under 3 sentences for simple query",
            "escalation_judgment": "No escalation needed — self-serve product search",
            "factual_accuracy": "Product details match catalog results from algolia_semantic_search",
        },
    },
    {
        "id": "m5-ce-002",
        "name": "Intent classification for billing issue",
        "category": "escalation",
        "domain": "customer_engagement",
        "query": (
            "I was charged twice for my subscription this month and I need this "
            "resolved immediately. This is completely unacceptable."
        ),
        "expected_tools": ["lex_classify_intent", "connect_escalate_to_human"],
        "evaluation_criteria": {
            "intent_accuracy": "Correctly classifies billing dispute intent via lex_classify_intent",
            "tone_appropriateness": "Acknowledges frustration before providing information",
            "escalation_judgment": "Correctly escalates billing dispute to human agent",
            "factual_accuracy": "Does not fabricate billing details or make price guarantees",
        },
    },
    {
        "id": "m5-ce-003",
        "name": "Personalized recommendations",
        "category": "recommendations",
        "domain": "customer_engagement",
        "query": (
            "I've been using your CI/CD tools for a year now. "
            "What other products would complement my current setup?"
        ),
        "expected_tools": ["personalize_get_recommendations", "algolia_semantic_search"],
        "evaluation_criteria": {
            "intent_accuracy": "Correctly identifies upsell/recommendation intent",
            "tone_appropriateness": "Warm tone that acknowledges customer loyalty",
            "escalation_judgment": "No escalation needed — recommendation request is in scope",
            "factual_accuracy": "Recommendations are grounded in personalize and catalog data",
        },
    },

    # -------------------------------------------------------------------------
    # Geospatial Intelligence domain (3 test cases)
    # Criteria: spatial_accuracy, tool_usage, data_freshness, completeness
    # -------------------------------------------------------------------------
    {
        "id": "m5-geo-001",
        "name": "Geocode and route planning",
        "category": "routing",
        "domain": "geospatial_intelligence",
        "query": (
            "What is the driving distance and estimated travel time between "
            "the AWS us-east-1 data center in Ashburn, VA and the us-east-2 "
            "data center in Columbus, OH?"
        ),
        "expected_tools": ["location_geocode", "location_calculate_route"],
        "evaluation_criteria": {
            "spatial_accuracy": "Coordinates and route distance match tool output, not memory estimates",
            "tool_usage": "Uses location_geocode then location_calculate_route — no memory-based estimates",
            "data_freshness": "Qualifies routing result as an estimate subject to traffic conditions",
            "completeness": "Includes distance, travel time, and start/end coordinates in response",
        },
    },
    {
        "id": "m5-geo-002",
        "name": "Nearby infrastructure search",
        "category": "poi_search",
        "domain": "geospatial_intelligence",
        "query": (
            "Find co-location facilities within 50 km of our office at "
            "1 Infinite Loop, Cupertino, CA that support cross-connects."
        ),
        "expected_tools": ["location_search_nearby", "mapbox_poi_search"],
        "evaluation_criteria": {
            "spatial_accuracy": "Search radius and returned POI coordinates are accurate per tool output",
            "tool_usage": "Uses location_search_nearby and mapbox_poi_search rather than listing from memory",
            "data_freshness": "Notes that facility availability data may require direct verification",
            "completeness": "Lists facility names, distances, and addresses from tool results",
        },
    },
    {
        "id": "m5-geo-003",
        "name": "Isochrone analysis",
        "category": "isochrone",
        "domain": "geospatial_intelligence",
        "query": (
            "What area can our field engineers reach within 30 minutes of driving "
            "from our Seattle office at 2nd Ave & Pike St?"
        ),
        "expected_tools": ["mapbox_isochrone", "mapbox_forward_geocode"],
        "evaluation_criteria": {
            "spatial_accuracy": "Isochrone polygon and origin coordinates match tool output",
            "tool_usage": "Uses mapbox_forward_geocode for origin then mapbox_isochrone for reachability",
            "data_freshness": "Qualifies that isochrone is based on typical traffic, not real-time",
            "completeness": "Describes reachable area with geographic landmarks or bounding coordinates",
        },
    },

    # -------------------------------------------------------------------------
    # Voice Interaction domain (3 test cases)
    # Criteria: response_brevity, speech_naturalness, transcription_handling, latency_awareness
    # -------------------------------------------------------------------------
    {
        "id": "m5-voice-001",
        "name": "Audio transcription request",
        "category": "transcription",
        "domain": "voice_interaction",
        "query": (
            "Please transcribe the audio file at s3://my-bucket/meeting-recording.wav "
            "and give me a summary."
        ),
        "expected_tools": ["deepgram_transcribe", "transcribe_audio"],
        "evaluation_criteria": {
            "response_brevity": "Summary response is 3 sentences or fewer",
            "speech_naturalness": "No markdown, bullet points, or formatted text in spoken response",
            "transcription_handling": "Uses deepgram_transcribe and transcribe_audio; handles low-confidence words",
            "latency_awareness": "Response length is appropriate for voice delivery without excessive detail",
        },
    },
    {
        "id": "m5-voice-002",
        "name": "Text-to-speech synthesis",
        "category": "synthesis",
        "domain": "voice_interaction",
        "query": (
            "Synthesize the following status update for our on-call engineer: "
            "'Deployment to production completed successfully at 14:32 UTC.'"
        ),
        "expected_tools": ["polly_synthesize", "deepgram_synthesize"],
        "evaluation_criteria": {
            "response_brevity": "Confirmation response is 1-2 sentences",
            "speech_naturalness": "Output text is clean spoken language with no formatting artifacts",
            "transcription_handling": "N/A — synthesis task, not transcription",
            "latency_awareness": "Chooses synthesis parameters appropriate for low-latency delivery",
        },
    },
    {
        "id": "m5-voice-003",
        "name": "Voice pipeline end-to-end",
        "category": "pipeline",
        "domain": "voice_interaction",
        "query": (
            "Transcribe the incoming audio from the support call, then synthesize "
            "a spoken acknowledgment response for the caller."
        ),
        "expected_tools": ["deepgram_transcribe", "polly_synthesize"],
        "evaluation_criteria": {
            "response_brevity": "Spoken acknowledgment is 1-2 sentences, not a full transcript",
            "speech_naturalness": "Synthesized response uses natural conversational language",
            "transcription_handling": "Transcribes audio first before generating acknowledgment",
            "latency_awareness": "Pipeline is structured to minimize round-trip latency",
        },
    },
]

# Evaluation criteria descriptions for Module 5 — all three domains
MODULE5_EVALUATION_CRITERIA = {
    # Customer Engagement criteria
    "intent_accuracy": (
        "Does the agent correctly identify the customer's primary intent "
        "(e.g., product search, billing dispute, recommendation request)?"
    ),
    "tone_appropriateness": (
        "Does the response match the brand tone guidelines — warm, professional, "
        "under 3 sentences for simple queries, acknowledging the customer's concern first?"
    ),
    "escalation_judgment": (
        "Does the agent correctly decide when to escalate to a human agent via "
        "connect_escalate_to_human versus handling the request autonomously?"
    ),
    "factual_accuracy": (
        "Is product and account information accurate per catalog results from "
        "algolia_semantic_search and personalize_get_recommendations?"
    ),

    # Geospatial Intelligence criteria
    "spatial_accuracy": (
        "Are coordinates, distances, and routing results correct per tool output "
        "rather than estimated from the model's internal knowledge?"
    ),
    "tool_usage": (
        "Does the agent use geospatial tools (location_*, mapbox_*) for all spatial "
        "computation instead of estimating from memory?"
    ),
    "data_freshness": (
        "Does the agent flag when spatial data may be stale, cached, or subject to "
        "real-time conditions such as traffic?"
    ),
    "completeness": (
        "Does the response include all relevant spatial dimensions — coordinates, "
        "distances, travel times, or reachable area — as appropriate for the query?"
    ),

    # Voice Interaction criteria
    "response_brevity": (
        "Is the spoken response 3 sentences or fewer, appropriate for voice delivery "
        "without overwhelming the listener?"
    ),
    "speech_naturalness": (
        "Is the output free of markdown, code blocks, bullet points, URLs, and other "
        "formatting artifacts that would sound unnatural when spoken aloud?"
    ),
    "transcription_handling": (
        "Does the agent correctly invoke transcription tools and handle low-confidence "
        "transcription results with appropriate clarification requests?"
    ),
    "latency_awareness": (
        "Is the response length and synthesis configuration appropriate for the voice "
        "latency budget, avoiding unnecessarily long outputs?"
    ),
}
