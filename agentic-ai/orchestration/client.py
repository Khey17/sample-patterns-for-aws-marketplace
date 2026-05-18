"""
orchestration/client.py
========================
Client for starting workflows, sending signals, and querying state.

Usage:
    import asyncio
    from orchestration.client import start_workflow, send_approval, query_stage

    wf_id = asyncio.run(start_workflow("/app/nodejs-api"))
    asyncio.run(send_approval(wf_id, approved=True, reviewer="platform-team"))
"""

from __future__ import annotations

import uuid
from typing import Any

from temporalio.client import Client

from orchestration.config import TemporalConnectionConfig
from orchestration.tracing import get_tracing_interceptor
from orchestration.dataclasses import (
    WorkflowInput,
    WorkflowResult,
    ApprovalDecision,
)
from orchestration.workflows.devops_companion import DevOpsCompanionWorkflow


async def get_client(config: TemporalConnectionConfig | None = None) -> Client:
    """Connect to the Temporal server."""
    config = config or TemporalConnectionConfig()
    interceptor = get_tracing_interceptor()
    connect_kwargs: dict = {
        "target_host": config.endpoint,
        "namespace": config.namespace,
        "interceptors": [interceptor],
    }
    if config.use_tls:
        connect_kwargs["tls"] = True
        connect_kwargs["api_key"] = config.api_key
    return await Client.connect(**connect_kwargs)


async def start_workflow(
    repo_path: str,
    region: str = "us-east-1",
    environment: str = "dev",
    demo_mode: bool = False,
    config: TemporalConnectionConfig | None = None,
) -> str:
    """Start a DevOps Companion workflow. Returns the workflow ID."""
    config = config or TemporalConnectionConfig()
    client = await get_client(config)
    workflow_id = f"devops-companion-{uuid.uuid4().hex[:8]}"

    await client.start_workflow(
        DevOpsCompanionWorkflow.run,
        WorkflowInput(repo_path=repo_path, region=region, environment=environment, demo_mode=demo_mode),
        id=workflow_id,
        task_queue=config.task_queue,
    )
    return workflow_id


async def send_continue(
    workflow_id: str,
    config: TemporalConnectionConfig | None = None,
) -> None:
    """Send the continue signal to a demo-mode workflow paused after mapping."""
    client = await get_client(config)
    handle = client.get_workflow_handle(workflow_id)
    await handle.signal(DevOpsCompanionWorkflow.continue_to_verification)


async def send_approval(
    workflow_id: str,
    approved: bool,
    reviewer: str,
    comments: str = "",
    config: TemporalConnectionConfig | None = None,
) -> None:
    """Send an approval/rejection signal to a waiting workflow."""
    client = await get_client(config)
    handle = client.get_workflow_handle(workflow_id)
    await handle.signal(
        DevOpsCompanionWorkflow.approve_deployment,
        ApprovalDecision(approved=approved, reviewer=reviewer, comments=comments),
    )


async def query_stage(
    workflow_id: str,
    config: TemporalConnectionConfig | None = None,
) -> str:
    """Query the current stage of a workflow."""
    client = await get_client(config)
    handle = client.get_workflow_handle(workflow_id)
    return await handle.query(DevOpsCompanionWorkflow.current_stage)


async def get_result(
    workflow_id: str,
    config: TemporalConnectionConfig | None = None,
) -> WorkflowResult:
    """Wait for and return the workflow result."""
    client = await get_client(config)
    handle = client.get_workflow_handle(workflow_id)
    raw = await handle.result()
    if isinstance(raw, WorkflowResult):
        return raw
    return WorkflowResult(**raw)


async def start_saga_workflow(
    force_failure_at: str = "configure_dns",
    config: TemporalConnectionConfig | None = None,
) -> str:
    """Start a standalone DeploymentSagaWorkflow. Returns workflow ID."""
    from orchestration.workflows.deployment_saga import DeploymentSagaWorkflow
    from orchestration.dataclasses import SagaInput

    config = config or TemporalConnectionConfig()
    client = await get_client(config)
    workflow_id = f"deployment-saga-{uuid.uuid4().hex[:8]}"

    await client.start_workflow(
        DeploymentSagaWorkflow.run,
        SagaInput(cdk_stacks=5, force_failure_at=force_failure_at),
        id=workflow_id,
        task_queue=config.task_queue,
    )
    return workflow_id


async def get_saga_result(
    workflow_id: str,
    config: TemporalConnectionConfig | None = None,
) -> "SagaResult":
    """Wait for and return the saga workflow result."""
    from orchestration.dataclasses import SagaResult

    client = await get_client(config)
    handle = client.get_workflow_handle(workflow_id)
    raw = await handle.result()
    if isinstance(raw, SagaResult):
        return raw
    return SagaResult(**raw)


async def is_temporal_reachable(
    config: TemporalConnectionConfig | None = None,
) -> bool:
    """Check if the Temporal server is reachable."""
    try:
        await get_client(config)
        return True
    except Exception:
        return False
