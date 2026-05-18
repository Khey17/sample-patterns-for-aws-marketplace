"""
tests/test_module6_tools.py
============================
Tests for Module 6 workflows and activities in mock mode.
"""

from __future__ import annotations

import os

import pytest

os.environ["AGENT_MOCK_MODE"] = "true"
os.environ["AGENT_NO_DELAY"] = "true"

from module6.workflows.devops_companion import DevOpsCompanionWorkflow
from module6.activities.analysis import analyze_repository, map_dependencies
from module6.activities.generation import generate_cdk
from module6.activities.deployment import deploy_to_ecs
from module6.activities.verification import static_security_scan, compliance_check, smoke_tests
from module6.activities.observability import setup_observability, get_workflow_traces
from module6.mock.temporal_mocks import get_mock_temporal_client, MockTemporalClient


# ---------------------------------------------------------------------------
# Activity tests
# ---------------------------------------------------------------------------

class TestAnalysisActivities:
    def test_analyze_repository(self):
        result = analyze_repository("/app/repo", "us-east-1")
        assert result["activity"] == "analyze_repository"
        assert result["mock_mode"] is True
        assert len(result["aws_services_needed"]) > 0
        assert result["estimated_stacks"] > 0

    def test_map_dependencies(self):
        analysis = {"aws_services_needed": ["ECS", "RDS", "S3"]}
        result = map_dependencies(analysis)
        assert result["activity"] == "map_dependencies"
        assert result["total_dependencies"] == 3
        assert len(result["mappings"]) == 3

    def test_map_dependencies_empty(self):
        result = map_dependencies({"aws_services_needed": []})
        assert result["total_dependencies"] == 0


class TestGenerationActivity:
    def test_generate_cdk(self):
        deps = {"mappings": [{"service": "ECS"}]}
        result = generate_cdk(deps)
        assert result["activity"] == "generate_cdk"
        assert result["stacks_generated"] == 5
        assert result["syntax_valid"] is True
        assert result["total_resources"] > 0


class TestDeploymentActivity:
    def test_deploy_to_ecs(self):
        result = deploy_to_ecs()
        assert result["activity"] == "deploy_to_ecs"
        assert result["status"] == "DEPLOYED"
        assert result["running_count"] >= result["desired_count"]
        assert len(result["steps"]) == 3
        assert result["heartbeat_count"] > 0


class TestVerificationActivities:
    def test_static_security_scan(self):
        cdk_output = {"stacks_generated": 5}
        result = static_security_scan(cdk_output)
        assert result["activity"] == "static_security_scan"
        assert result["passed"] is True
        assert result["summary"]["critical"] == 0

    def test_compliance_check(self):
        cdk_output = {"stacks_generated": 5}
        result = compliance_check(cdk_output)
        assert result["activity"] == "compliance_check"
        assert result["passed"] is True
        assert result["blocking"] is False
        assert "tagging" in result["categories_checked"]

    def test_smoke_tests(self):
        deployment = {"service_name": "test-service"}
        result = smoke_tests(deployment)
        assert result["activity"] == "smoke_tests"
        assert result["overall"] == "PASSED"
        assert result["tests_passed"] == result["tests_run"]


class TestObservabilityActivities:
    def test_setup_observability(self):
        deployment = {"service_name": "api-service"}
        result = setup_observability(deployment)
        assert result["activity"] == "setup_observability"
        assert result["alarms_configured"] == 3

    def test_get_workflow_traces(self):
        result = get_workflow_traces("test-workflow-123")
        assert result["workflow_id"] == "test-workflow-123"
        assert len(result["spans"]) > 0
        assert result["bedrock_calls"] > 0
        assert "datadog_trace_url" in result


# ---------------------------------------------------------------------------
# Temporal mock client tests
# ---------------------------------------------------------------------------

class TestMockTemporalClient:
    def setup_method(self):
        self.client = MockTemporalClient()

    def test_start_workflow(self):
        result = self.client.start_workflow(
            "DevOpsCompanionWorkflow",
            {"repo": "/app"},
        )
        assert result["status"] == "RUNNING"
        assert result["mock_mode"] is True
        assert "workflow_id" in result

    def test_execute_activity(self):
        start = self.client.start_workflow("test", {})
        wf_id = start["workflow_id"]

        result = self.client.execute_activity(wf_id, "analyze_repository")
        assert result["status"] == "COMPLETED"
        assert result["checkpoint_number"] == 1

    def test_checkpoint_increments(self):
        start = self.client.start_workflow("test", {})
        wf_id = start["workflow_id"]

        self.client.execute_activity(wf_id, "analyze_repository")
        self.client.execute_activity(wf_id, "map_dependencies")
        result = self.client.execute_activity(wf_id, "generate_cdk")
        assert result["checkpoint_number"] == 3

    def test_pause_and_signal(self):
        start = self.client.start_workflow("test", {})
        wf_id = start["workflow_id"]

        pause = self.client.pause_for_signal(wf_id)
        assert pause["status"] == "WAITING_FOR_SIGNAL"
        assert "workflow_id" in pause

        # Cannot execute activity while paused
        blocked = self.client.execute_activity(wf_id, "deploy_to_ecs")
        assert "error" in blocked

        # Signal resumes
        signal = self.client.signal_workflow(wf_id, "approve_deployment", {"approved": True})
        assert signal["signal_delivered"] is True
        assert signal["workflow_status"] == "RUNNING"

    def test_query_workflow(self):
        start = self.client.start_workflow("test", {})
        wf_id = start["workflow_id"]
        self.client.execute_activity(wf_id, "analyze_repository")

        state = self.client.query_workflow(wf_id)
        assert state["checkpoint_count"] == 1
        assert "analyze_repository" in state["activities_completed"]
        assert state["status"] == "RUNNING"

    def test_workflow_completes(self):
        start = self.client.start_workflow("test", {})
        wf_id = start["workflow_id"]

        from module6.mock.temporal_mocks import PIPELINE_ACTIVITIES
        for act in PIPELINE_ACTIVITIES:
            self.client.execute_activity(wf_id, act["name"])

        state = self.client.query_workflow(wf_id)
        assert state["status"] == "COMPLETED"

    def test_crash_and_replay(self):
        start = self.client.start_workflow("test", {})
        wf_id = start["workflow_id"]

        self.client.execute_activity(wf_id, "analyze_repository")
        self.client.execute_activity(wf_id, "map_dependencies")

        result = self.client.simulate_crash_and_replay(wf_id, "map_dependencies")
        assert result["recovery"] == "REPLAY"
        assert result["skipped_re_execution"] is True
        assert "analyze_repository" in result["replayed_activities"]
        assert "map_dependencies" in result["replayed_activities"]
        assert result["resumed_from"] == "generate_cdk"

    def test_get_workflow_history(self):
        start = self.client.start_workflow("test", {})
        wf_id = start["workflow_id"]
        self.client.execute_activity(wf_id, "analyze_repository")

        history = self.client.get_workflow_history(wf_id)
        assert history["total_events"] > 1
        assert history["events"][0]["event_type"] == "WorkflowExecutionStarted"

    def test_worker_info(self):
        info = self.client.get_worker_info()
        assert len(info["workers"]) == 4
        assert info["max_concurrent_activities"] == 5

    def test_saga_forward_execution(self):
        start = self.client.start_workflow("test", {})
        wf_id = start["workflow_id"]

        r1 = self.client.execute_saga_step(wf_id, "create_cdk_stack", "delete_cdk_stack")
        assert r1["compensation_registered"] == "delete_cdk_stack"
        assert r1["saga_step"] == 1

        r2 = self.client.execute_saga_step(wf_id, "create_security_group", "remove_security_group")
        assert r2["saga_step"] == 2

        r3 = self.client.execute_saga_step(wf_id, "deploy_ecs_service", "delete_ecs_service")
        assert r3["saga_step"] == 3

        state = self.client.query_workflow(wf_id)
        assert state["checkpoint_count"] == 3

    def test_saga_compensation_on_failure(self):
        start = self.client.start_workflow("test", {})
        wf_id = start["workflow_id"]

        self.client.execute_saga_step(wf_id, "create_cdk_stack", "delete_cdk_stack")
        self.client.execute_saga_step(wf_id, "create_security_group", "remove_security_group")
        self.client.execute_saga_step(wf_id, "deploy_ecs_service", "delete_ecs_service")

        result = self.client.trigger_saga_compensation(wf_id, "configure_dns")

        assert result["failure_at"] == "configure_dns"
        assert result["saga_steps_completed"] == 3
        assert result["final_status"] == "COMPENSATED"
        assert result["compensation_order"] == [
            "delete_ecs_service",
            "remove_security_group",
            "delete_cdk_stack",
        ]


# ---------------------------------------------------------------------------
# Workflow integration tests
# ---------------------------------------------------------------------------

class TestDevOpsCompanionWorkflow:
    def test_full_pipeline_auto_approve(self):
        wf = DevOpsCompanionWorkflow()
        wf.start("/app/repo", "us-east-1")

        analysis = wf.run_analysis("/app/repo", "us-east-1")
        assert "analysis" in analysis

        cdk = wf.run_generation(analysis["dependencies"])
        assert cdk["stacks_generated"] > 0

        verification = wf.run_parallel_verification(cdk)
        assert verification["security_scan"]["passed"] is True
        assert verification["compliance_check"]["passed"] is True

        pause = wf.pause_for_approval()
        assert pause["status"] == "WAITING_FOR_SIGNAL"

        approval = wf.submit_approval(True, "test-user", "approved")
        assert approval["signal_delivered"] is True

        deploy = wf.run_deployment()
        assert deploy["status"] == "DEPLOYED"

        tests = wf.run_smoke_tests(deploy)
        assert tests["overall"] == "PASSED"

        obs = wf.run_observability_setup(deploy)
        assert obs["alarms_configured"] > 0

        status = wf.get_status()
        assert status["status"] == "COMPLETED"

    def test_rejected_pipeline(self):
        wf = DevOpsCompanionWorkflow()
        wf.start("/app/repo")
        wf.run_analysis("/app/repo")
        wf.run_generation({"mappings": []})
        wf.pause_for_approval()

        result = wf.submit_approval(False, "reviewer", "needs Multi-AZ")
        assert result["signal_delivered"] is True

    def test_get_traces(self):
        wf = DevOpsCompanionWorkflow()
        wf.start("/app/repo")
        traces = wf.get_traces()
        assert "trace_id" in traces
        assert "spans" in traces
