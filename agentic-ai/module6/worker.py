"""
module6/worker.py
==================
Temporal worker entrypoint — runs on ECS Fargate.

In production, this process polls the Temporal Cloud task queue and
executes activities. It runs as a long-lived container on ECS Fargate
with configurable concurrency limits.

Usage (production):
    python -m module6.worker

Usage (demo):
    This file shows the worker configuration pattern. The demo
    uses MockTemporalClient directly rather than starting a real worker.
"""

from __future__ import annotations

import asyncio
import os


WORKER_CONFIG = {
    "task_queue": "devops-companion",
    "max_concurrent_activities": 5,
    "max_concurrent_workflow_tasks": 10,
    "graceful_shutdown_timeout_seconds": 30,
}


async def run_worker() -> None:
    """Start a Temporal worker (production mode).

    This is the code that would run inside each ECS Fargate task.
    Workers poll the task queue and execute activities locally.
    """
    temporal_endpoint = os.getenv("TEMPORAL_ENDPOINT", "localhost:7233")
    temporal_namespace = os.getenv("TEMPORAL_NAMESPACE", "devops-companion")
    api_key = os.getenv("TEMPORAL_API_KEY")

    if not api_key:
        print("[Worker] No TEMPORAL_API_KEY set — cannot start real worker.")
        print("[Worker] Use the demo script (demos/module6_demo.py) for mock mode.")
        return

    try:
        from temporalio.client import Client
        from temporalio.worker import Worker

        from module6.activities.analysis import analyze_repository, map_dependencies
        from module6.activities.generation import generate_cdk
        from module6.activities.deployment import deploy_to_ecs
        from module6.activities.verification import static_security_scan, compliance_check, smoke_tests
        from module6.activities.observability import setup_observability

        client = await Client.connect(
            temporal_endpoint,
            namespace=temporal_namespace,
            api_key=api_key,
            tls=True,
        )

        worker = Worker(
            client,
            task_queue=WORKER_CONFIG["task_queue"],
            activities=[
                analyze_repository,
                map_dependencies,
                generate_cdk,
                static_security_scan,
                compliance_check,
                deploy_to_ecs,
                smoke_tests,
                setup_observability,
            ],
            max_concurrent_activities=WORKER_CONFIG["max_concurrent_activities"],
            max_concurrent_workflow_tasks=WORKER_CONFIG["max_concurrent_workflow_tasks"],
        )

        print(f"[Worker] Starting on task queue: {WORKER_CONFIG['task_queue']}")
        print(f"[Worker] Max concurrent activities: {WORKER_CONFIG['max_concurrent_activities']}")
        print(f"[Worker] Connecting to: {temporal_endpoint}/{temporal_namespace}")
        await worker.run()

    except ImportError:
        print("[Worker] temporalio package not installed.")
        print("[Worker] Install with: pip install temporalio")
    except Exception as e:
        print(f"[Worker] Failed to start: {e}")


if __name__ == "__main__":
    asyncio.run(run_worker())
