"""
module6/workflows/devops_companion.py
=======================================
DevOps Companion workflow — the Temporal workflow definition.

In production, this would use @workflow.defn and @workflow.run decorators
from the Temporal SDK. For the demo, we orchestrate activities through
the MockTemporalClient which simulates checkpointing and replay.

The workflow proceeds through these stages:
1.  analyze_repository (Bedrock)
2.  map_dependencies (deterministic)
3.  generate_cdk (Bedrock)
4a. static_security_scan (deterministic)  ─┐ parallel
4b. compliance_check (deterministic)      ─┘
5.  [SIGNAL WAIT] approve_deployment (human-in-the-loop)
6.  deploy_to_ecs (long-running, heartbeats)
7.  smoke_tests
8.  setup_observability
"""

from __future__ import annotations

from typing import Any

from module6.mock.temporal_mocks import get_mock_temporal_client
from module6.activities.analysis import analyze_repository, map_dependencies
from module6.activities.generation import generate_cdk
from module6.activities.deployment import deploy_to_ecs
from module6.activities.verification import static_security_scan, compliance_check, smoke_tests
from module6.activities.observability import setup_observability, get_workflow_traces


class DevOpsCompanionWorkflow:
    """Orchestrates the full DevOps Companion pipeline via Temporal.

    Each method corresponds to a phase of the workflow. The mock
    Temporal client tracks checkpoints and supports signal-based
    approval gates.
    """

    def __init__(self) -> None:
        self._client = get_mock_temporal_client()
        self._workflow_id: str | None = None

    def start(self, repo_path: str, region: str = "us-east-1") -> dict[str, Any]:
        """Start a new workflow execution."""
        result = self._client.start_workflow(
            workflow_name="DevOpsCompanionWorkflow",
            workflow_input={"repo_path": repo_path, "region": region},
            task_queue="devops-companion",
        )
        self._workflow_id = result["workflow_id"]
        return result

    def run_analysis(self, repo_path: str, region: str = "us-east-1") -> dict[str, Any]:
        """Execute analysis activities (analyze + map dependencies)."""
        if not self._workflow_id:
            raise RuntimeError("Workflow not started")

        analysis = analyze_repository(repo_path, region)
        self._client.execute_activity(self._workflow_id, "analyze_repository")

        deps = map_dependencies(analysis)
        self._client.execute_activity(self._workflow_id, "map_dependencies")

        return {"analysis": analysis, "dependencies": deps}

    def run_generation(self, dependency_mapping: dict[str, Any]) -> dict[str, Any]:
        """Execute CDK generation activity."""
        if not self._workflow_id:
            raise RuntimeError("Workflow not started")

        cdk = generate_cdk(dependency_mapping)
        self._client.execute_activity(self._workflow_id, "generate_cdk")
        return cdk

    def pause_for_approval(self) -> dict[str, Any]:
        """Pause the workflow and wait for human approval signal."""
        if not self._workflow_id:
            raise RuntimeError("Workflow not started")

        return self._client.pause_for_signal(self._workflow_id, "approve_deployment")

    def submit_approval(self, approved: bool, reviewer: str, comments: str = "") -> dict[str, Any]:
        """Send approval/rejection signal to resume the workflow."""
        if not self._workflow_id:
            raise RuntimeError("Workflow not started")

        return self._client.signal_workflow(
            self._workflow_id,
            signal_name="approve_deployment",
            signal_data={
                "approved": approved,
                "reviewer": reviewer,
                "comments": comments,
            },
        )

    def run_static_security_scan(self, cdk_output: dict[str, Any]) -> dict[str, Any]:
        """Execute static security scan activity on CDK code."""
        if not self._workflow_id:
            raise RuntimeError("Workflow not started")

        result = static_security_scan(cdk_output)
        self._client.execute_activity(self._workflow_id, "static_security_scan")
        return result

    def run_compliance_check(self, cdk_output: dict[str, Any]) -> dict[str, Any]:
        """Execute compliance check activity on CDK code."""
        if not self._workflow_id:
            raise RuntimeError("Workflow not started")

        result = compliance_check(cdk_output)
        self._client.execute_activity(self._workflow_id, "compliance_check")
        return result

    def run_parallel_verification(self, cdk_output: dict[str, Any]) -> dict[str, Any]:
        """Execute static security scan and compliance check in parallel.

        In production Temporal, these would be concurrent execute_activity calls.
        """
        scan = self.run_static_security_scan(cdk_output)
        compliance = self.run_compliance_check(cdk_output)
        return {"security_scan": scan, "compliance_check": compliance}

    def run_deployment(self) -> dict[str, Any]:
        """Execute the ECS deployment activity (long-running)."""
        if not self._workflow_id:
            raise RuntimeError("Workflow not started")

        result = deploy_to_ecs()
        self._client.execute_activity(self._workflow_id, "deploy_to_ecs")
        return result

    def run_smoke_tests(self, deployment: dict[str, Any]) -> dict[str, Any]:
        """Execute post-deployment smoke tests."""
        if not self._workflow_id:
            raise RuntimeError("Workflow not started")

        result = smoke_tests(deployment)
        self._client.execute_activity(self._workflow_id, "smoke_tests")
        return result

    def run_observability_setup(self, deployment: dict[str, Any]) -> dict[str, Any]:
        """Configure observability for the deployed service."""
        if not self._workflow_id:
            raise RuntimeError("Workflow not started")

        result = setup_observability(deployment)
        self._client.execute_activity(self._workflow_id, "setup_observability")
        return result

    def get_status(self) -> dict[str, Any]:
        """Query current workflow state."""
        if not self._workflow_id:
            return {"error": "Workflow not started"}
        return self._client.query_workflow(self._workflow_id)

    def get_history(self) -> dict[str, Any]:
        """Get full workflow event history."""
        if not self._workflow_id:
            return {"error": "Workflow not started"}
        return self._client.get_workflow_history(self._workflow_id)

    def simulate_crash(self, crash_after: str) -> dict[str, Any]:
        """Simulate a crash and show Temporal replay recovery."""
        if not self._workflow_id:
            return {"error": "Workflow not started"}
        return self._client.simulate_crash_and_replay(self._workflow_id, crash_after)

    def get_traces(self) -> dict[str, Any]:
        """Get distributed traces for the workflow execution."""
        wf_id = self._workflow_id or "unknown"
        return get_workflow_traces(wf_id)

    def run_saga_deployment(self, steps: list[dict[str, str]]) -> dict[str, Any]:
        """Execute deployment steps with registered compensations.

        Each step is a dict with 'activity' and 'compensation' keys.
        """
        if not self._workflow_id:
            raise RuntimeError("Workflow not started")

        results = []
        for step in steps:
            result = self._client.execute_saga_step(
                self._workflow_id,
                activity_name=step["activity"],
                compensation_name=step["compensation"],
            )
            results.append(result)

        return {
            "workflow_id": self._workflow_id,
            "steps_completed": len(results),
            "saga_log": [
                {"activity": s["activity"], "compensation": s["compensation"]}
                for s in steps
            ],
        }

    def trigger_compensation(self, failure_at: str) -> dict[str, Any]:
        """Trigger saga compensation from a failure point."""
        if not self._workflow_id:
            raise RuntimeError("Workflow not started")
        return self._client.trigger_saga_compensation(self._workflow_id, failure_at)

    def get_worker_info(self) -> dict[str, Any]:
        """Get worker fleet status."""
        return self._client.get_worker_info()

    @property
    def workflow_id(self) -> str | None:
        return self._workflow_id
