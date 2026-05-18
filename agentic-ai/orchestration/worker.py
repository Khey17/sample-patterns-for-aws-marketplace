"""
orchestration/worker.py
========================
Temporal worker entrypoint.

Connects to either the local dev server or Temporal Cloud, then polls
the task queue and executes workflow and activity tasks.

Usage:
    # Dev server (temporal server start-dev must be running)
    python -m orchestration.worker

    # Temporal Cloud
    TEMPORAL_API_KEY=... TEMPORAL_ENDPOINT=ns.tmprl.cloud:7233 TEMPORAL_NAMESPACE=ns python -m orchestration.worker
"""

from __future__ import annotations

import asyncio

from temporalio.client import Client
from temporalio.worker import Worker

from orchestration.config import TemporalConnectionConfig
from orchestration.tracing import get_tracing_interceptor
from orchestration.workflows.devops_companion import DevOpsCompanionWorkflow
from orchestration.workflows.deployment_saga import DeploymentSagaWorkflow
from orchestration.activities.analysis import analyze_repository, map_dependencies
from orchestration.activities.generation import generate_cdk
from orchestration.activities.deployment import (
    deploy_to_ecs,
    rollback_deployment,
    create_cdk_stack,
    create_security_group,
    deploy_ecs_service,
    configure_dns,
    delete_cdk_stack,
    remove_security_group,
    delete_ecs_service,
    remove_dns_record,
)
from orchestration.activities.verification import (
    static_security_scan,
    compliance_check,
    smoke_tests,
)
from orchestration.activities.observability import setup_observability


async def run_worker(config: TemporalConnectionConfig | None = None) -> None:
    """Start a Temporal worker that processes DevOps Companion workflows."""
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

    client = await Client.connect(**connect_kwargs)

    worker = Worker(
        client,
        task_queue=config.task_queue,
        workflows=[DevOpsCompanionWorkflow, DeploymentSagaWorkflow],
        activities=[
            analyze_repository,
            map_dependencies,
            generate_cdk,
            deploy_to_ecs,
            rollback_deployment,
            create_cdk_stack,
            create_security_group,
            deploy_ecs_service,
            configure_dns,
            delete_cdk_stack,
            remove_security_group,
            delete_ecs_service,
            remove_dns_record,
            static_security_scan,
            compliance_check,
            smoke_tests,
            setup_observability,
        ],
    )

    mode = "Cloud" if config.is_cloud else "Dev Server"
    print(f"[Temporal Worker] Mode: {mode}")
    print(f"[Temporal Worker] Endpoint: {config.endpoint}")
    print(f"[Temporal Worker] Namespace: {config.namespace}")
    print(f"[Temporal Worker] Task queue: {config.task_queue}")
    print("[Temporal Worker] Polling for tasks...")

    await worker.run()


if __name__ == "__main__":
    asyncio.run(run_worker())
