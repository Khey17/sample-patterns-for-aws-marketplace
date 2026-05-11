# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""
module5/tools/transcribe_tools.py
===================================
Amazon Transcribe tool for the voice interaction domain.

Uses boto3 in live mode, falls back to mock data when
AGENT_MOCK_DOMAIN=true or when boto3 / credentials are unavailable.
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone

from langchain_core.tools import tool

from module5.mock.domain_mocks import mock_transcribe_audio

def _is_mock() -> bool:
    return os.getenv("AGENT_MOCK_DOMAIN", "true").lower() == "true"


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


@tool
def transcribe_audio(
    audio_s3_uri: str,
    language_code: str = "en-US",
    job_name: str = "",
) -> str:
    """Transcribe audio from S3 using Amazon Transcribe.

    Starts an Amazon Transcribe job for the given S3 audio URI and returns
    the job details. The job runs asynchronously; poll with
    get_transcription_job to check completion status.

    Args:
        audio_s3_uri: S3 URI of the audio file (e.g. s3://bucket/key.wav).
        language_code: BCP-47 language code for transcription (default: en-US).
        job_name: Unique job name; auto-generated from timestamp if empty.

    Returns:
        JSON string with Output_Envelope containing job name, status, and S3 URI.
    """
    resolved_job_name = job_name or f"transcribe-{int(time.time())}"

    if _is_mock():
        return json.dumps(
            mock_transcribe_audio(
                audio_s3_uri=audio_s3_uri,
                language_code=language_code,
                job_name=resolved_job_name,
            ),
            indent=2,
        )
    try:
        import boto3

        client = boto3.client("transcribe", region_name=os.getenv("AWS_REGION", "us-east-1"))
        client.start_transcription_job(
            TranscriptionJobName=resolved_job_name,
            Media={"MediaFileUri": audio_s3_uri},
            MediaFormat=audio_s3_uri.rsplit(".", 1)[-1] if "." in audio_s3_uri else "wav",
            LanguageCode=language_code,
        )
        return json.dumps(
            {
                "tool": "transcribe_audio",
                "timestamp": _timestamp(),
                "mock_mode": False,
                "data": {
                    "job_name": resolved_job_name,
                    "status": "IN_PROGRESS",
                    "language_code": language_code,
                    "audio_s3_uri": audio_s3_uri,
                    "message": "Transcription job started. Poll get_transcription_job for completion.",
                },
            },
            indent=2,
        )
    except (ImportError, KeyError):
        return json.dumps(
            mock_transcribe_audio(
                audio_s3_uri=audio_s3_uri,
                language_code=language_code,
                job_name=resolved_job_name,
            ),
            indent=2,
        )
    except Exception as e:
        return json.dumps(
            {
                "tool": "transcribe_audio",
                "timestamp": _timestamp(),
                "mock_mode": False,
                "data": {"error": str(e)},
            },
            indent=2,
        )
