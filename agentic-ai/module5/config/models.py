# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""
module5/config/models.py
========================
Model configuration for Module 5 Domain-Specific Agent Applications.

Uses LangChain's ChatBedrock interface with CRIS (Cross-Region Inference)
profiles for automatic failover across AWS regions.

Model selection guidance:
  - Sonnet 4.6 (default): domain agent reasoning, tool orchestration, complex queries
  - Haiku 4.5: lightweight tasks, intent classification, simple lookups
"""

from __future__ import annotations

import os
from typing import Any

from langchain_aws import ChatBedrock

# CRIS inference profile IDs
SONNET_4_6 = "us.anthropic.claude-sonnet-4-6"
HAIKU_4_5 = "us.anthropic.claude-haiku-4-5-20251001-v1:0"


def get_chat_bedrock_model(
    region: str | None = None,
    model_id: str = SONNET_4_6,
    temperature: float = 0.1,
    max_tokens: int = 4096,
    streaming: bool = False,
    **kwargs: Any,
) -> ChatBedrock:
    """
    Get a configured ChatBedrock model using CRIS inference profiles.

    Defaults to Claude Sonnet 4.6 via the US cross-region inference profile,
    which provides automatic failover across us-east-1, us-west-2, and
    us-east-2 for higher availability and throughput.

    Parameters
    ----------
    region : str, optional
        AWS region. Defaults to AWS_REGION env var or us-east-1.
    model_id : str
        CRIS inference profile ID. Use SONNET_4_6 (default) for domain agent
        reasoning, or HAIKU_4_5 for lightweight/fast tasks.
    temperature : float
        Sampling temperature (0.0–1.0). Default 0.1 for deterministic output.
    max_tokens : int
        Maximum tokens in response. Default 4096.
    streaming : bool
        Enable streaming responses.
    **kwargs
        Additional model_kwargs passed to ChatBedrock.

    Returns
    -------
    ChatBedrock
        Configured LangChain ChatBedrock model.

    Examples
    --------
    >>> # Default: Sonnet 4.6 for domain agent reasoning
    >>> model = get_chat_bedrock_model()

    >>> # Haiku 4.5 for lightweight tasks
    >>> from module5.config.models import HAIKU_4_5
    >>> model = get_chat_bedrock_model(model_id=HAIKU_4_5, max_tokens=1024)
    """
    aws_region = region or os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION") or "us-east-1"

    return ChatBedrock(
        model_id=model_id,
        region_name=aws_region,
        model_kwargs={
            "temperature": temperature,
            "max_tokens": max_tokens,
            **kwargs,
        },
        streaming=streaming,
    )


def get_haiku_model(
    region: str | None = None,
    temperature: float = 0.0,
    max_tokens: int = 1024,
    **kwargs: Any,
) -> ChatBedrock:
    """
    Convenience function for Haiku 4.5 — fast, low-cost tasks.

    Use for: intent classification, simple lookups, guardrail checks,
    evaluation scoring, and any task where latency matters more than depth.
    """
    return get_chat_bedrock_model(
        region=region,
        model_id=HAIKU_4_5,
        temperature=temperature,
        max_tokens=max_tokens,
        **kwargs,
    )
