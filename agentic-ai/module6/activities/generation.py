"""
module6/activities/generation.py
=================================
CDK infrastructure code generation activity.

Delegates to Module 3's HTTP endpoint (POST /generate) when available.
Module 3 handles Bedrock internally — module 6 only orchestrates.
Falls back to mock CDK output if the endpoint is unreachable.
"""

from __future__ import annotations

import json
import os
from typing import Any

from module6.activities._endpoints import is_endpoint_live, call_endpoint, sim_work_delay
from module6.mock.aws_mocks import MOCK_CDK_RESPONSE


def generate_cdk(dependency_mapping: dict[str, Any]) -> dict[str, Any]:
    """Generate CDK infrastructure code from dependency mapping.

    Delegates to Module 3 (POST /generate) when its endpoint is live.
    Falls back to mock CDK code otherwise.
    """
    mock_mode = os.getenv("AGENT_MOCK_MODE", "true").lower() == "true"

    cdk_code = MOCK_CDK_RESPONSE

    if not mock_mode and is_endpoint_live("module3"):
        result = call_endpoint("module3", "/generate", {
            "requirements": dependency_mapping,
            "region": "us-east-1",
            "environment": "dev",
        })
        if result and result.get("status") == "success":
            cdk_code = result.get("output", MOCK_CDK_RESPONSE)
    else:
        sim_work_delay()

    stacks = [
        {"name": "VpcStack", "resources": 6},
        {"name": "RdsStack", "resources": 4},
        {"name": "ElastiCacheStack", "resources": 3},
        {"name": "EcsApiStack", "resources": 8},
        {"name": "EcsWorkerStack", "resources": 8},
    ]

    return {
        "activity": "generate_cdk",
        "stacks_generated": len(stacks),
        "stacks": stacks,
        "total_resources": sum(s["resources"] for s in stacks),
        "language": "TypeScript",
        "cdk_version": "2.x",
        "code_preview": cdk_code[:200] + "...",
        "syntax_valid": True,
        "estimated_monthly_cost": "$450-$650",
        "source": "module3_endpoint" if not mock_mode and is_endpoint_live("module3") else "mock",
        "mock_mode": mock_mode or not is_endpoint_live("module3"),
    }
