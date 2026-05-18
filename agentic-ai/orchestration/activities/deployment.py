"""
orchestration/activities/deployment.py
========================================
ECS deployment activity with heartbeat reporting.
"""

from __future__ import annotations

import asyncio

from temporalio import activity

from orchestration.dataclasses import CdkResult, DeploymentResult


@activity.defn
async def deploy_to_ecs(cdk: CdkResult) -> DeploymentResult:
    """Deploy application to ECS Fargate.

    Reports heartbeats so Temporal can detect worker failures during
    this long-running activity and retry on another worker.
    """
    activity.heartbeat("creating_service")
    await asyncio.sleep(2)

    activity.heartbeat("waiting_for_stability")
    await asyncio.sleep(3)

    activity.heartbeat("verifying_health")
    await asyncio.sleep(1)

    return DeploymentResult(
        cluster="devops-companion",
        service_name="api-service",
        task_definition="devops-companion-api:3",
        status="DEPLOYED",
        running_count=2,
        desired_count=2,
        deployment_duration_seconds=50,
    )


@activity.defn
async def rollback_deployment(step_name: str) -> str:
    """Compensation activity: roll back a deployment step."""
    activity.heartbeat(f"rolling_back_{step_name}")
    await asyncio.sleep(1)
    return f"rolled_back:{step_name}"


@activity.defn
async def create_cdk_stack(should_fail: bool = False) -> str:
    """Saga step: create CDK stack."""
    activity.heartbeat("create_cdk_stack")
    await asyncio.sleep(1)
    if should_fail:
        raise RuntimeError("CDK stack creation failed")
    return "completed:create_cdk_stack"


@activity.defn
async def create_security_group(should_fail: bool = False) -> str:
    """Saga step: create security group."""
    activity.heartbeat("create_security_group")
    await asyncio.sleep(1)
    if should_fail:
        raise RuntimeError("Security group creation failed")
    return "completed:create_security_group"


@activity.defn
async def deploy_ecs_service(should_fail: bool = False) -> str:
    """Saga step: deploy ECS service."""
    activity.heartbeat("deploy_ecs_service")
    await asyncio.sleep(1)
    if should_fail:
        raise RuntimeError("ECS service deployment failed")
    return "completed:deploy_ecs_service"


@activity.defn
async def configure_dns(should_fail: bool = False) -> str:
    """Saga step: configure DNS."""
    activity.heartbeat("configure_dns")
    await asyncio.sleep(1)
    if should_fail:
        raise RuntimeError("DNS validation timeout: CNAME propagation failed")
    return "completed:configure_dns"


@activity.defn
async def delete_cdk_stack() -> str:
    """Compensation: delete CDK stack."""
    activity.heartbeat("delete_cdk_stack")
    await asyncio.sleep(0.5)
    return "compensated:delete_cdk_stack"


@activity.defn
async def remove_security_group() -> str:
    """Compensation: remove security group."""
    activity.heartbeat("remove_security_group")
    await asyncio.sleep(0.5)
    return "compensated:remove_security_group"


@activity.defn
async def delete_ecs_service() -> str:
    """Compensation: delete ECS service."""
    activity.heartbeat("delete_ecs_service")
    await asyncio.sleep(0.5)
    return "compensated:delete_ecs_service"


@activity.defn
async def remove_dns_record() -> str:
    """Compensation: remove DNS record."""
    activity.heartbeat("remove_dns_record")
    await asyncio.sleep(0.5)
    return "compensated:remove_dns_record"
