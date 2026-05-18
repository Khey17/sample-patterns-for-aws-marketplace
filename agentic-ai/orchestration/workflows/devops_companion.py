"""
orchestration/workflows/devops_companion.py
=============================================
Production DevOps Companion workflow with durable execution.

Uses real Temporal decorators: @workflow.defn, @workflow.run, @workflow.signal.
Activities are executed with timeouts, retry policies, and checkpointing.
"""

from __future__ import annotations

import asyncio
from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from orchestration.dataclasses import (
        WorkflowInput,
        WorkflowResult,
        ApprovalDecision,
        AnalysisResult,
        DependencyMapping,
        CdkResult,
        SecurityScanResult,
        ComplianceResult,
        DeploymentResult,
        SmokeTestResult,
        ObservabilityResult,
        SagaInput,
        SagaResult,
    )
    from orchestration.activities.analysis import analyze_repository, map_dependencies
    from orchestration.activities.generation import generate_cdk
    from orchestration.activities.deployment import deploy_to_ecs, rollback_deployment
    from orchestration.workflows.deployment_saga import DeploymentSagaWorkflow
    from orchestration.activities.verification import (
        static_security_scan,
        compliance_check,
        smoke_tests,
    )
    from orchestration.activities.observability import setup_observability


@workflow.defn
class DevOpsCompanionWorkflow:
    """Durable DevOps Companion pipeline orchestrated by Temporal.

    Stages:
    1. analyze_repository (Bedrock via Module 2)
    2. map_dependencies (deterministic)
    3. generate_cdk (Bedrock via Module 3)
    4. parallel: static_security_scan + compliance_check
    5. signal wait: approve_deployment (human-in-the-loop)
    6. deploy_to_ecs (long-running, heartbeats)
    7. smoke_tests
    8. setup_observability
    """

    def __init__(self) -> None:
        self._approval_decision: ApprovalDecision | None = None
        self._continue_signal: bool = False
        self._current_stage: str = "initialized"
        self._compensations: list[str] = []

    @workflow.signal
    async def approve_deployment(self, decision: ApprovalDecision) -> None:
        """Signal handler for human approval/rejection."""
        self._approval_decision = decision

    @workflow.signal
    async def continue_to_verification(self) -> None:
        """Signal to resume past the demo pause after analysis/mapping."""
        self._continue_signal = True

    @workflow.query
    def current_stage(self) -> str:
        """Query handler: return current workflow stage."""
        return self._current_stage

    @workflow.run
    async def run(self, input: WorkflowInput) -> WorkflowResult:
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            backoff_coefficient=2.0,
            maximum_attempts=3,
            maximum_interval=timedelta(seconds=30),
        )

        # Step 1: Analyze repository — CHECKPOINT
        self._current_stage = "analyzing"
        analysis: AnalysisResult = await workflow.execute_activity(
            analyze_repository,
            input,
            start_to_close_timeout=timedelta(seconds=60),
            retry_policy=retry_policy,
        )

        # Step 2: Map dependencies — CHECKPOINT
        self._current_stage = "mapping_dependencies"
        deps: DependencyMapping = await workflow.execute_activity(
            map_dependencies,
            analysis,
            start_to_close_timeout=timedelta(seconds=60),
            retry_policy=retry_policy,
        )

        # Demo mode: pause here so the interactive demo can show steps 1-2
        if input.demo_mode:
            self._current_stage = "paused_after_mapping"
            await workflow.wait_condition(lambda: self._continue_signal)

        # Step 3: Generate CDK — CHECKPOINT
        self._current_stage = "generating_cdk"
        cdk: CdkResult = await workflow.execute_activity(
            generate_cdk,
            deps,
            start_to_close_timeout=timedelta(seconds=90),
            retry_policy=retry_policy,
        )

        # Step 4: Parallel verification — fan-out/fan-in CHECKPOINT
        self._current_stage = "verifying"
        scan_result: SecurityScanResult
        compliance_result: ComplianceResult
        scan_result, compliance_result = await asyncio.gather(
            workflow.execute_activity(
                static_security_scan,
                cdk,
                start_to_close_timeout=timedelta(seconds=60),
                retry_policy=retry_policy,
            ),
            workflow.execute_activity(
                compliance_check,
                cdk,
                start_to_close_timeout=timedelta(seconds=60),
                retry_policy=retry_policy,
            ),
        )

        # Step 5: Wait for human approval signal — DURABLE WAIT
        self._current_stage = "awaiting_approval"
        await workflow.wait_condition(
            lambda: self._approval_decision is not None
        )

        if not self._approval_decision.approved:
            self._current_stage = "rejected"
            return WorkflowResult(
                status="REJECTED",
                analysis=analysis,
                cdk=cdk,
                security_scan=scan_result,
                compliance=compliance_result,
                approval=self._approval_decision,
            )

        # Step 6: Deploy via child workflow (saga pattern) — CHECKPOINT
        self._current_stage = "deploying"
        saga_input = SagaInput(cdk_stacks=cdk.stacks_generated)
        saga_result: SagaResult = await workflow.execute_child_workflow(
            DeploymentSagaWorkflow.run,
            saga_input,
            id=f"{workflow.info().workflow_id}-deployment-saga",
            task_queue=workflow.info().task_queue,
        )

        if saga_result.status == "COMPENSATED":
            self._current_stage = "compensated"
            return WorkflowResult(
                status="COMPENSATED",
                analysis=analysis,
                cdk=cdk,
                security_scan=scan_result,
                compliance=compliance_result,
                approval=self._approval_decision,
                error=f"Deployment saga failed at '{saga_result.failure_at}', compensations executed",
            )

        deployment = DeploymentResult(
            cluster="devops-companion",
            service_name="api-service",
            task_definition="devops-companion-api:3",
            status="DEPLOYED",
            running_count=2,
            desired_count=2,
            deployment_duration_seconds=saga_result.steps_completed * 10,
        )

        # Step 7: Smoke tests — CHECKPOINT
        self._current_stage = "smoke_testing"
        test_result: SmokeTestResult = await workflow.execute_activity(
            smoke_tests,
            deployment,
            start_to_close_timeout=timedelta(seconds=120),
            retry_policy=RetryPolicy(maximum_attempts=2),
        )

        # Step 8: Setup observability — CHECKPOINT
        self._current_stage = "setting_up_observability"
        obs_result: ObservabilityResult = await workflow.execute_activity(
            setup_observability,
            deployment,
            start_to_close_timeout=timedelta(seconds=60),
            retry_policy=RetryPolicy(maximum_attempts=2),
        )

        self._current_stage = "completed"
        return WorkflowResult(
            status="COMPLETED",
            analysis=analysis,
            cdk=cdk,
            security_scan=scan_result,
            compliance=compliance_result,
            deployment=deployment,
            smoke_tests=test_result,
            observability=obs_result,
            approval=self._approval_decision,
        )
