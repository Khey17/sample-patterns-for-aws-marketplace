"""
module6/activities/deployment.py
=================================
ECS deployment activity — long-running with heartbeats.

This is the critical activity that benefits most from Temporal's
durability. Deploying to ECS takes minutes and involves multiple
sub-steps (create service, wait for stability, verify health).
If the worker crashes mid-deployment, Temporal replays the workflow
and resumes from the last checkpoint.
"""

from __future__ import annotations

import os
import time
from typing import Any

from module6.activities._endpoints import sim_work_delay
from module6.mock.aws_mocks import (
    mock_create_ecs_service,
    mock_describe_ecs_services,
    mock_ecs_wait_stable,
)


def deploy_to_ecs(
    cluster: str = "devops-companion",
    service_name: str = "api-service",
    task_definition: str = "devops-companion-api:3",
    desired_count: int = 2,
) -> dict[str, Any]:
    """Deploy application to ECS Fargate.

    This is a long-running activity that reports heartbeats. In production,
    Temporal uses heartbeats to detect worker failures — if no heartbeat
    arrives within the timeout, the activity is retried on another worker.

    Steps:
    1. Create/update ECS service
    2. Wait for service to reach steady state
    3. Verify running count matches desired count
    """
    mock_mode = os.getenv("AGENT_MOCK_MODE", "true").lower() == "true"
    steps_completed = []

    # Step 1: Create/update service
    sim_work_delay()
    create_result = mock_create_ecs_service(cluster, service_name, task_definition)
    steps_completed.append({
        "step": "create_service",
        "status": "completed",
        "service_arn": create_result["service"]["serviceArn"],
    })

    # Step 2: Wait for steady state (heartbeat interval)
    sim_work_delay()
    stable_result = mock_ecs_wait_stable(cluster, service_name)
    steps_completed.append({
        "step": "wait_for_stability",
        "status": "completed",
        "wait_time_seconds": stable_result["wait_time_seconds"],
    })

    # Step 3: Verify health
    sim_work_delay()
    describe_result = mock_describe_ecs_services(cluster, [service_name])
    service = describe_result["services"][0]
    healthy = service["runningCount"] >= desired_count
    steps_completed.append({
        "step": "verify_health",
        "status": "completed" if healthy else "failed",
        "running_count": service["runningCount"],
        "desired_count": desired_count,
    })

    return {
        "activity": "deploy_to_ecs",
        "cluster": cluster,
        "service_name": service_name,
        "task_definition": task_definition,
        "status": "DEPLOYED" if healthy else "UNHEALTHY",
        "steps": steps_completed,
        "running_count": service["runningCount"],
        "desired_count": desired_count,
        "deployment_duration_seconds": stable_result["wait_time_seconds"] + 5,
        "heartbeat_count": 3,
        "mock_mode": mock_mode,
    }
