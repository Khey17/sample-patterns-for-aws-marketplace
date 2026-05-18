"""
orchestration/workflows/deployment_saga.py
============================================
Deployment Saga workflow — child workflow demonstrating saga compensation.

Runs multi-step infrastructure deployment with registered compensations.
If any step fails, compensations execute in reverse order to restore
the system to a consistent state.

Used as a child workflow from DevOpsCompanionWorkflow, or standalone
for demo purposes (section 5).
"""

from __future__ import annotations

from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from orchestration.dataclasses import SagaInput, SagaResult
    from orchestration.activities.deployment import (
        create_cdk_stack,
        create_security_group,
        deploy_ecs_service,
        configure_dns,
        delete_cdk_stack,
        remove_security_group,
        delete_ecs_service,
        remove_dns_record,
    )


SAGA_STEPS = [
    (create_cdk_stack, delete_cdk_stack, "create_cdk_stack"),
    (create_security_group, remove_security_group, "create_security_group"),
    (deploy_ecs_service, delete_ecs_service, "deploy_ecs_service"),
    (configure_dns, remove_dns_record, "configure_dns"),
]


@workflow.defn
class DeploymentSagaWorkflow:
    """Multi-step deployment with saga compensation on failure.

    Each forward step registers a compensation. If any step fails,
    all registered compensations execute in reverse order.
    """

    def __init__(self) -> None:
        self._current_step: str = "initialized"
        self._force_failure_at: str | None = None

    @workflow.signal
    async def force_failure(self, step_name: str) -> None:
        """Signal to force a failure at a specific step (for demos)."""
        self._force_failure_at = step_name

    @workflow.query
    def current_step(self) -> str:
        """Query the current deployment step."""
        return self._current_step

    @workflow.run
    async def run(self, input: SagaInput) -> SagaResult:
        retry_policy = RetryPolicy(maximum_attempts=2)
        compensations: list[str] = []
        steps_completed = 0

        # Use input-level failure point or wait for signal
        failure_at = input.force_failure_at or self._force_failure_at

        try:
            for activity_fn, compensation_fn, step_name in SAGA_STEPS:
                self._current_step = step_name
                compensations.append((compensation_fn, step_name))

                if failure_at == step_name:
                    # Execute activity with failure flag — no retries so it fails fast
                    await workflow.execute_activity(
                        activity_fn,
                        True,
                        start_to_close_timeout=timedelta(seconds=60),
                        retry_policy=RetryPolicy(maximum_attempts=1),
                    )
                else:
                    await workflow.execute_activity(
                        activity_fn,
                        start_to_close_timeout=timedelta(seconds=60),
                        retry_policy=retry_policy,
                    )
                steps_completed += 1

        except Exception as ex:
            # Saga compensation: execute in reverse order
            self._current_step = "compensating"
            compensations_executed: list[str] = []

            for compensation_fn, step_name in reversed(compensations):
                try:
                    await workflow.execute_activity(
                        compensation_fn,
                        start_to_close_timeout=timedelta(seconds=60),
                        retry_policy=retry_policy,
                    )
                    compensations_executed.append(step_name)
                except Exception:
                    workflow.logger.error(f"Compensation {step_name} failed")

            self._current_step = "compensated"
            return SagaResult(
                status="COMPENSATED",
                steps_completed=steps_completed,
                compensations_executed=compensations_executed,
                failure_at=failure_at or "",
            )

        self._current_step = "deployed"
        return SagaResult(
            status="DEPLOYED",
            steps_completed=steps_completed,
            compensations_executed=[],
            failure_at="",
        )
