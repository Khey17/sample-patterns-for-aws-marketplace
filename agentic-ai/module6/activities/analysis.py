"""
module6/activities/analysis.py
===============================
Repository analysis and dependency mapping activities.

These activities delegate to Module 2's HTTP endpoint when available.
Module 2 handles Bedrock internally — module 6 only orchestrates.
Falls back to mock responses if the endpoint is unreachable.
"""

from __future__ import annotations

import os
from typing import Any

from module6.activities._endpoints import is_endpoint_live, call_endpoint, sim_work_delay
from module6.mock.aws_mocks import MOCK_ANALYSIS_RESPONSE


def analyze_repository(repo_path: str, region: str = "us-east-1") -> dict[str, Any]:
    """Analyze a code repository's structure, frameworks, and deployment needs.

    Delegates to Module 2 (POST /analyze) when its endpoint is live.
    Falls back to mock data otherwise.
    """
    mock_mode = os.getenv("AGENT_MOCK_MODE", "true").lower() == "true"

    if not mock_mode and is_endpoint_live("module2"):
        result = call_endpoint("module2", "/analyze", {"repo_path": repo_path})
        if result and "error" not in result:
            analysis_text = result.get("analysis", MOCK_ANALYSIS_RESPONSE)
            return {
                "activity": "analyze_repository",
                "repo_path": repo_path,
                "region": region,
                "analysis": analysis_text,
                "frameworks_detected": ["express", "flask"],
                "languages": ["typescript", "python"],
                "aws_services_needed": ["ECS", "RDS", "ElastiCache", "S3", "ALB"],
                "estimated_stacks": 5,
                "source": "module2_endpoint",
                "mock_mode": False,
            }

    sim_work_delay()
    return {
        "activity": "analyze_repository",
        "repo_path": repo_path,
        "region": region,
        "analysis": MOCK_ANALYSIS_RESPONSE,
        "frameworks_detected": ["express", "flask"],
        "languages": ["typescript", "python"],
        "aws_services_needed": ["ECS", "RDS", "ElastiCache", "S3", "ALB"],
        "estimated_stacks": 5,
        "source": "mock",
        "mock_mode": True,
    }


def map_dependencies(analysis: dict[str, Any]) -> dict[str, Any]:
    """Map detected dependencies to specific AWS service configurations.

    Takes the output of analyze_repository and produces a dependency
    mapping suitable for CDK generation. This is a deterministic
    transformation — no LLM call needed.
    """
    sim_work_delay()
    services = analysis.get("aws_services_needed", [])
    mappings = []
    for svc in services:
        mappings.append({
            "service": svc,
            "construct": f"aws-cdk-lib/aws-{svc.lower()}",
            "configuration": {
                "high_availability": True,
                "multi_az": svc in ("RDS", "ElastiCache"),
                "encryption_at_rest": True,
            },
        })

    return {
        "activity": "map_dependencies",
        "total_dependencies": len(mappings),
        "mappings": mappings,
        "deployment_target": "ECS Fargate",
        "networking": "VPC with private subnets",
        "mock_mode": analysis.get("mock_mode", True),
    }
