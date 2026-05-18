"""
tests/test_orchestration.py
=============================
Tests for the real Temporal orchestration package.

Uses temporalio.testing.WorkflowEnvironment.start_local() which runs
an in-process Temporal test server — no external server needed.
"""

import asyncio
import json

import pytest
from dataclasses import asdict

from orchestration import is_available
from orchestration.config import TemporalConnectionConfig
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
)


# ---------------------------------------------------------------------------
# Unit tests (no Temporal server needed)
# ---------------------------------------------------------------------------


class TestOrchestrationAvailability:
    def test_is_available(self):
        assert is_available() is True


class TestConfig:
    def test_default_dev_server(self):
        cfg = TemporalConnectionConfig()
        assert cfg.endpoint == "localhost:7233"
        assert cfg.namespace == "default"
        assert cfg.api_key is None
        assert cfg.use_tls is False
        assert cfg.is_dev_server is True
        assert cfg.is_cloud is False

    def test_cloud_mode(self, monkeypatch):
        monkeypatch.setenv("TEMPORAL_API_KEY", "test-key-123")
        monkeypatch.setenv("TEMPORAL_ENDPOINT", "ns.tmprl.cloud:7233")
        monkeypatch.setenv("TEMPORAL_NAMESPACE", "my-namespace")
        cfg = TemporalConnectionConfig()
        assert cfg.api_key == "test-key-123"
        assert cfg.endpoint == "ns.tmprl.cloud:7233"
        assert cfg.namespace == "my-namespace"
        assert cfg.use_tls is True
        assert cfg.is_cloud is True
        assert cfg.is_dev_server is False


class TestDataclasses:
    def test_workflow_input_defaults(self):
        inp = WorkflowInput(repo_path="/app/test")
        assert inp.region == "us-east-1"
        assert inp.environment == "dev"

    def test_approval_decision_serializable(self):
        decision = ApprovalDecision(approved=True, reviewer="tester", comments="ok")
        d = asdict(decision)
        assert d == {"approved": True, "reviewer": "tester", "comments": "ok"}

    def test_workflow_result_defaults(self):
        result = WorkflowResult(status="COMPLETED")
        assert result.analysis is None
        assert result.error == ""

    def test_all_dataclasses_json_serializable(self):
        """All dataclass fields must be JSON-serializable for Temporal."""
        objects = [
            WorkflowInput(repo_path="/test"),
            AnalysisResult(repo_path="/test", region="us-east-1", analysis="test"),
            DependencyMapping(total_dependencies=0),
            CdkResult(stacks_generated=5),
            SecurityScanResult(stacks_scanned=5),
            ComplianceResult(stacks_checked=5),
            DeploymentResult(),
            SmokeTestResult(),
            ObservabilityResult(),
            ApprovalDecision(approved=True, reviewer="test"),
            WorkflowResult(status="COMPLETED"),
        ]
        for obj in objects:
            serialized = json.dumps(asdict(obj))
            assert serialized is not None


# ---------------------------------------------------------------------------
# Integration tests (uses in-process Temporal test server)
# ---------------------------------------------------------------------------


def _get_all_activities():
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

    return [
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
    ]


def _get_all_workflows():
    from orchestration.workflows.devops_companion import DevOpsCompanionWorkflow
    from orchestration.workflows.deployment_saga import DeploymentSagaWorkflow
    return [DevOpsCompanionWorkflow, DeploymentSagaWorkflow]


class TestWorkflowIntegration:
    """Tests that run real workflows against the in-process Temporal server."""

    def test_full_pipeline_approved(self):
        """Run the complete workflow with auto-approval."""
        from temporalio.testing import WorkflowEnvironment
        from temporalio.worker import Worker
        from orchestration.workflows.devops_companion import DevOpsCompanionWorkflow

        async def _run():
            async with await WorkflowEnvironment.start_local() as env:
                task_queue = "test-approved"
                async with Worker(
                    env.client,
                    task_queue=task_queue,
                    workflows=_get_all_workflows(),
                    activities=_get_all_activities(),
                ):
                    handle = await env.client.start_workflow(
                        DevOpsCompanionWorkflow.run,
                        WorkflowInput(repo_path="/app/nodejs-api", region="us-east-1"),
                        id="test-wf-approved",
                        task_queue=task_queue,
                    )

                    # Wait for the workflow to reach the approval gate
                    for _ in range(60):
                        stage = await handle.query(DevOpsCompanionWorkflow.current_stage)
                        if stage == "awaiting_approval":
                            break
                        await asyncio.sleep(0.3)
                    assert stage == "awaiting_approval"

                    # Send approval signal
                    await handle.signal(
                        DevOpsCompanionWorkflow.approve_deployment,
                        ApprovalDecision(approved=True, reviewer="test-user", comments="auto"),
                    )

                    # Wait for result
                    result: WorkflowResult = await handle.result()
                    assert result.status == "COMPLETED"
                    assert result.analysis is not None
                    assert result.analysis.source in ("mock", "module2_endpoint")
                    assert result.deployment is not None
                    assert result.deployment.running_count == 2
                    assert result.smoke_tests is not None
                    assert result.smoke_tests.overall == "PASSED"
                    assert result.observability is not None
                    assert result.approval.approved is True

        asyncio.run(_run())

    def test_full_pipeline_rejected(self):
        """Run the workflow and reject at the approval gate."""
        from temporalio.testing import WorkflowEnvironment
        from temporalio.worker import Worker
        from orchestration.workflows.devops_companion import DevOpsCompanionWorkflow

        async def _run():
            async with await WorkflowEnvironment.start_local() as env:
                task_queue = "test-rejected"
                async with Worker(
                    env.client,
                    task_queue=task_queue,
                    workflows=_get_all_workflows(),
                    activities=_get_all_activities(),
                ):
                    handle = await env.client.start_workflow(
                        DevOpsCompanionWorkflow.run,
                        WorkflowInput(repo_path="/app/test-reject"),
                        id="test-wf-rejected",
                        task_queue=task_queue,
                    )

                    # Wait for approval gate
                    for _ in range(60):
                        stage = await handle.query(DevOpsCompanionWorkflow.current_stage)
                        if stage == "awaiting_approval":
                            break
                        await asyncio.sleep(0.3)

                    # Reject
                    await handle.signal(
                        DevOpsCompanionWorkflow.approve_deployment,
                        ApprovalDecision(approved=False, reviewer="security-team", comments="Needs fixes"),
                    )

                    result: WorkflowResult = await handle.result()
                    assert result.status == "REJECTED"
                    assert result.deployment is None
                    assert result.approval.reviewer == "security-team"

        asyncio.run(_run())

    def test_query_current_stage(self):
        """Test that the workflow query handler returns the current stage."""
        from temporalio.testing import WorkflowEnvironment
        from temporalio.worker import Worker
        from orchestration.workflows.devops_companion import DevOpsCompanionWorkflow

        async def _run():
            async with await WorkflowEnvironment.start_local() as env:
                task_queue = "test-query"
                async with Worker(
                    env.client,
                    task_queue=task_queue,
                    workflows=_get_all_workflows(),
                    activities=_get_all_activities(),
                ):
                    handle = await env.client.start_workflow(
                        DevOpsCompanionWorkflow.run,
                        WorkflowInput(repo_path="/app/query-test"),
                        id="test-wf-query",
                        task_queue=task_queue,
                    )

                    # Poll until we reach the approval gate
                    for _ in range(60):
                        stage = await handle.query(DevOpsCompanionWorkflow.current_stage)
                        if stage == "awaiting_approval":
                            break
                        await asyncio.sleep(0.3)
                    assert stage == "awaiting_approval"

                    # Approve to let it complete
                    await handle.signal(
                        DevOpsCompanionWorkflow.approve_deployment,
                        ApprovalDecision(approved=True, reviewer="test", comments=""),
                    )

                    result = await handle.result()
                    assert result.status == "COMPLETED"

        asyncio.run(_run())
