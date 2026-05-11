# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""
Guardrail Configuration — Bedrock Guardrails integration for domain agents.

Translates GuardrailPolicy dataclass into Bedrock Guardrails API calls.
Supports mock mode via AGENT_MOCK_DOMAIN env var.
"""
from __future__ import annotations

import os
from typing import Any

from module5.engine.domain_adapter import GuardrailPolicy

# ---------------------------------------------------------------------------
# Module-level mock flag — re-evaluated per call to support test overrides
# ---------------------------------------------------------------------------

_SENSITIVE_KEYWORDS = {"password", "secret", "ssn", "credit card", "api key", "access key"}


def _is_mock() -> bool:
    return os.getenv("AGENT_MOCK_DOMAIN", "true").lower() == "true"



# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_guardrail(policy: GuardrailPolicy, domain_name: str) -> str | None:
    """
    Create a Bedrock Guardrail from a domain policy.

    In mock mode returns ``"mock-guardrail-{domain_name}"``.
    In live mode calls ``bedrock.create_guardrail()`` and returns the guardrailId.
    Returns None on any failure — never raises.

    Requirements: 4.1, 4.2, 4.3, 4.4, 13.4
    """
    if _is_mock():
        return f"mock-guardrail-{domain_name}"

    try:
        import boto3

        aws_region = os.getenv("AWS_REGION", "us-east-1")
        client = boto3.client("bedrock", region_name=aws_region)
        guardrail_name = f"module5-{domain_name}-guardrail"

        # Check if a guardrail with this name already exists and reuse it
        existing = client.list_guardrails()
        for g in existing.get("guardrails", []):
            if g["name"] == guardrail_name:
                return g["id"]

        kwargs: dict[str, Any] = {
            "name": guardrail_name,
            "description": f"Guardrail for {domain_name} domain agent",
            "blockedInputMessaging": "I cannot process this request.",
            "blockedOutputsMessaging": "I cannot provide this information.",
            "sensitiveInformationPolicyConfig": {
                "piiEntitiesConfig": [
                    {"type": entity, "action": policy.pii_handling}
                    for entity in policy.pii_entities
                ]
            },
        }

        if policy.denied_topics:
            kwargs["topicPolicyConfig"] = {
                "topicsConfig": [
                    {
                        "name": t["name"],
                        "definition": t["definition"],
                        "type": t.get("type", "DENY"),
                        "examples": t.get("examples", []),
                    }
                    for t in policy.denied_topics
                ]
            }

        if policy.content_filters:
            kwargs["contentPolicyConfig"] = {
                "filtersConfig": [
                    {"type": cat, "inputStrength": strength, "outputStrength": strength}
                    for cat, strength in policy.content_filters.items()
                ]
            }

        if policy.word_filters:
            kwargs["wordPolicyConfig"] = {
                "wordsConfig": [{"text": w} for w in policy.word_filters]
            }

        response = client.create_guardrail(**kwargs)
        return response["guardrailId"]

    except Exception:
        return None


def apply_guardrail_check(
    guardrail_id: str,
    guardrail_version: str,
    content: str,
    source: str = "INPUT",
) -> dict:
    """
    Apply a guardrail to content using the ApplyGuardrail API.

    Returns a dict with ``"action"`` set to ``"NONE"`` or
    ``"GUARDRAIL_INTERVENED"``.  When intervened, includes an ``"outputs"``
    key with sanitized text.  Never raises — returns an error dict on failure.

    Requirements: 4.5, 4.6, 4.7, 4.8, 13.5
    """
    if _is_mock():
        return _mock_guardrail_check(content)

    try:
        import boto3

        aws_region = os.getenv("AWS_REGION", "us-east-1")
        client = boto3.client("bedrock-runtime", region_name=aws_region)

        response = client.apply_guardrail(
            guardrailIdentifier=guardrail_id,
            guardrailVersion=guardrail_version,
            source=source,
            content=[{"text": {"text": content}}],
        )

        action = response.get("action", "NONE")
        result: dict[str, Any] = {"action": action}

        if action == "GUARDRAIL_INTERVENED":
            outputs = response.get("outputs", [])
            result["outputs"] = outputs

        return result

    except Exception as e:
        return {"action": "ERROR", "error": str(e)}


# ---------------------------------------------------------------------------
# Mock helpers
# ---------------------------------------------------------------------------

def _mock_guardrail_check(content: str) -> dict:
    """Simulate a guardrail check with simple keyword matching."""
    content_lower = content.lower()
    triggered = any(kw in content_lower for kw in _SENSITIVE_KEYWORDS)

    if triggered:
        sanitized = content
        for kw in _SENSITIVE_KEYWORDS:
            import re
            sanitized = re.sub(re.escape(kw), "[REDACTED]", sanitized, flags=re.IGNORECASE)
        return {
            "action": "GUARDRAIL_INTERVENED",
            "outputs": [{"text": sanitized}],
        }

    return {"action": "NONE"}
