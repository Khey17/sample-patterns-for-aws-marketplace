# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""
module5/tools/polly_tools.py
==============================
Amazon Polly text-to-speech tool for the voice interaction domain.

Uses boto3 in live mode, falls back to mock data when
AGENT_MOCK_DOMAIN=true or when boto3 / credentials are unavailable.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone

from langchain_core.tools import tool

from module5.mock.domain_mocks import mock_polly_synthesize

def _is_mock() -> bool:
    return os.getenv("AGENT_MOCK_DOMAIN", "true").lower() == "true"


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


@tool
def polly_synthesize(
    text: str,
    voice_id: str = "Joanna",
    output_format: str = "mp3",
    engine: str = "neural",
) -> str:
    """Synthesize text to speech using Amazon Polly.

    Converts text to audio using Amazon Polly's neural TTS engine and returns
    synthesis metadata. Binary audio is not streamed in tool output; use the
    returned metadata to retrieve the audio from S3 or trigger a download.

    Args:
        text: Text to synthesize into speech.
        voice_id: Polly voice ID (default: Joanna).
        output_format: Audio output format — mp3, ogg_vorbis, or pcm (default: mp3).
        engine: Polly engine — neural or standard (default: neural).

    Returns:
        JSON string with Output_Envelope containing voice_id, engine,
        character_count, output_format, and content_type.
    """
    if _is_mock():
        return json.dumps(
            mock_polly_synthesize(
                text=text,
                voice_id=voice_id,
                output_format=output_format,
                engine=engine,
            ),
            indent=2,
        )
    try:
        import boto3

        client = boto3.client("polly", region_name=os.getenv("AWS_REGION", "us-east-1"))
        response = client.synthesize_speech(
            Text=text,
            VoiceId=voice_id,
            OutputFormat=output_format,
            Engine=engine,
        )
        return json.dumps(
            {
                "tool": "polly_synthesize",
                "timestamp": _timestamp(),
                "mock_mode": False,
                "data": {
                    "input_text": text,
                    "voice_id": voice_id,
                    "output_format": output_format,
                    "engine": engine,
                    "character_count": len(text),
                    "content_type": response.get("ContentType", f"audio/{output_format}"),
                    "request_characters": response.get("RequestCharacters", len(text)),
                    "message": "Audio stream available. Retrieve via AudioStream in the raw response.",
                },
            },
            indent=2,
        )
    except (ImportError, KeyError):
        return json.dumps(
            mock_polly_synthesize(
                text=text,
                voice_id=voice_id,
                output_format=output_format,
                engine=engine,
            ),
            indent=2,
        )
    except Exception as e:
        return json.dumps(
            {
                "tool": "polly_synthesize",
                "timestamp": _timestamp(),
                "mock_mode": False,
                "data": {"error": str(e)},
            },
            indent=2,
        )
