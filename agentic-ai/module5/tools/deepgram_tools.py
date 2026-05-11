# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""
module5/tools/deepgram_tools.py
================================
Deepgram Voice AI tools for the voice interaction domain.

Uses the Deepgram SDK v6 in live mode, falls back to mock data when
AGENT_MOCK_DOMAIN=true or when the SDK / credentials are unavailable.

SDK v6 API:
  Transcription: client.listen.v1.media.transcribe_file(request=<bytes>, model=..., language=...)
  Synthesis:     client.speak.v1.audio.generate(text=..., model=...)
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone

from langchain_core.tools import tool

from module5.mock.domain_mocks import mock_deepgram_transcribe, mock_deepgram_synthesize


def _is_mock() -> bool:
    return os.getenv("AGENT_MOCK_DOMAIN", "true").lower() == "true"


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _fetch_audio_bytes(audio_source: str) -> bytes:
    """Load audio bytes from a local file path, file:// URI, S3 URI, or HTTPS URL.

    For security, only https:// URLs are accepted over HTTP — plain http://,
    ftp://, and other schemes are rejected. file:// and s3:// are handled via
    explicit branches that don't invoke urlopen.
    """
    if audio_source.startswith("file://"):
        with open(audio_source[7:], "rb") as f:
            return f.read()
    elif audio_source.startswith("s3://"):
        import boto3
        parts = audio_source[5:].split("/", 1)
        bucket, key = parts[0], parts[1]
        s3 = boto3.client("s3", region_name=os.getenv("AWS_REGION", "us-east-1"))
        obj = s3.get_object(Bucket=bucket, Key=key)
        return obj["Body"].read()
    elif audio_source.startswith("https://"):
        import urllib.request
        # Scheme verified above; urlopen restricted to https only.
        with urllib.request.urlopen(audio_source) as r:  # nosec B310
            return r.read()
    else:
        raise ValueError(
            f"Unsupported audio source scheme. Use file://, s3://, or https:// URLs. Got: {audio_source[:50]}"
        )


@tool
def deepgram_transcribe(audio_url: str, model: str = "nova-3", language: str = "en-US") -> str:
    """Transcribe audio to text using Deepgram Voice AI Nova-3.

    Downloads audio from an S3 URI or HTTPS URL and transcribes it using
    Deepgram Nova-3 with word-level confidence scores.

    Args:
        audio_url: S3 URI (s3://bucket/key) or HTTPS URL of the audio file.
        model: Deepgram model to use (default: nova-3).
        language: BCP-47 language code (default: en-US).

    Returns:
        JSON string with Output_Envelope containing transcript and confidence.
    """
    if _is_mock():
        return json.dumps(
            mock_deepgram_transcribe(audio_url=audio_url, model=model, language=language),
            indent=2,
        )
    try:
        from deepgram import DeepgramClient

        audio_bytes = _fetch_audio_bytes(audio_url)
        client = DeepgramClient(api_key=os.environ["DEEPGRAM_API_KEY"])
        response = client.listen.v1.media.transcribe_file(
            request=audio_bytes,
            model=model,
            language=language,
        )
        results = response.results
        alt = results.channels[0].alternatives[0] if results.channels else None
        transcript = alt.transcript if alt else ""
        confidence = alt.confidence if alt else 0.0
        return json.dumps(
            {
                "tool": "deepgram_transcribe",
                "timestamp": _timestamp(),
                "mock_mode": False,
                "data": {
                    "audio_url": audio_url,
                    "model": model,
                    "language": language,
                    "transcript": transcript,
                    "confidence": confidence,
                },
            },
            indent=2,
        )
    except (ImportError, KeyError):
        return json.dumps(
            mock_deepgram_transcribe(audio_url=audio_url, model=model, language=language),
            indent=2,
        )
    except Exception as e:
        return json.dumps(
            {
                "tool": "deepgram_transcribe",
                "timestamp": _timestamp(),
                "mock_mode": False,
                "data": {"error": str(e)},
            },
            indent=2,
        )


@tool
def deepgram_synthesize(text: str, voice: str = "aura-2-asteria-en", model: str = "aura-2") -> str:
    """Synthesize text to speech using Deepgram Aura-2.

    Converts text to audio using Deepgram's Aura-2 TTS model and saves
    the output to a temp file, returning the path and metadata.

    Args:
        text: Text to synthesize into speech.
        voice: Deepgram Aura-2 voice model (default: aura-2-asteria-en).
        model: Deepgram TTS model family (default: aura-2).

    Returns:
        JSON string with Output_Envelope containing output path and metadata.
    """
    if _is_mock():
        return json.dumps(
            mock_deepgram_synthesize(text=text, voice=voice, model=model),
            indent=2,
        )
    try:
        import tempfile
        from deepgram import DeepgramClient

        client = DeepgramClient(api_key=os.environ["DEEPGRAM_API_KEY"])
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            output_path = f.name

        chunks = list(client.speak.v1.audio.generate(text=text, model=voice))
        with open(output_path, "wb") as f:
            for chunk in chunks:
                f.write(chunk)

        return json.dumps(
            {
                "tool": "deepgram_synthesize",
                "timestamp": _timestamp(),
                "mock_mode": False,
                "data": {
                    "input_text": text,
                    "voice": voice,
                    "model": model,
                    "output_path": output_path,
                    "character_count": len(text),
                    "format": "mp3",
                },
            },
            indent=2,
        )
    except (ImportError, KeyError):
        return json.dumps(
            mock_deepgram_synthesize(text=text, voice=voice, model=model),
            indent=2,
        )
    except Exception as e:
        return json.dumps(
            {
                "tool": "deepgram_synthesize",
                "timestamp": _timestamp(),
                "mock_mode": False,
                "data": {"error": str(e)},
            },
            indent=2,
        )
