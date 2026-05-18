"""
orchestration/activities/observability.py
==========================================
Observability setup activity.
"""

from __future__ import annotations

import asyncio

from temporalio import activity

from orchestration.dataclasses import DeploymentResult, ObservabilityResult


@activity.defn
async def setup_observability(deployment: DeploymentResult) -> ObservabilityResult:
    """Configure CloudWatch alarms and monitoring for the deployment."""
    await asyncio.sleep(0.5)

    alarms = [
        {"name": f"{deployment.service_name}-HighCPU", "metric": "CPUUtilization", "threshold": 80},
        {"name": f"{deployment.service_name}-ErrorRate", "metric": "5XXError", "threshold": 5},
        {"name": f"{deployment.service_name}-Latency", "metric": "TargetResponseTime", "threshold": 2.0},
    ]

    return ObservabilityResult(
        service=deployment.service_name,
        alarms_configured=len(alarms),
        alarms=alarms,
        otlp_export_enabled=True,
    )
