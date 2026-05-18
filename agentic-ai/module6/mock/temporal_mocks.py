"""
module6/mock/temporal_mocks.py
===============================
Mock Temporal workflow client for Module 6 demos.

Simulates workflow execution, activity checkpointing, signal delivery,
replay behavior, and OpenTelemetry trace generation without requiring a
real Temporal Cloud connection.
"""

from __future__ import annotations

import random
import time
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any


def _sim_temporal_delay() -> None:
    """Sleep 0.5-1.5s to simulate Temporal server round-trip.

    Skipped when AGENT_NO_DELAY=true (e.g., in test suites).
    """
    import os
    if os.getenv("AGENT_NO_DELAY", "").lower() == "true":
        return
    time.sleep(random.uniform(0.5, 1.5))


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str = "wf") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


# Activities in the DevOps Companion workflow (execution order)
# Steps 4a/4b (static_security_scan + compliance_check) run in parallel.
PIPELINE_ACTIVITIES = [
    {"name": "analyze_repository", "typical_duration_s": 8, "uses_bedrock": True},
    {"name": "map_dependencies", "typical_duration_s": 5, "uses_bedrock": False},
    {"name": "generate_cdk", "typical_duration_s": 12, "uses_bedrock": True},
    {"name": "static_security_scan", "typical_duration_s": 6, "uses_bedrock": False},
    {"name": "compliance_check", "typical_duration_s": 5, "uses_bedrock": False},
    {"name": "deploy_to_ecs", "typical_duration_s": 180, "uses_bedrock": False},
    {"name": "smoke_tests", "typical_duration_s": 30, "uses_bedrock": False},
    {"name": "setup_observability", "typical_duration_s": 10, "uses_bedrock": False},
]


class MockTemporalClient:
    """In-memory mock of a Temporal workflow client.

    Tracks workflow state so the demo can show checkpoints, signals,
    replay, and query behavior realistically.
    """

    def __init__(self) -> None:
        self._workflows: dict[str, dict[str, Any]] = {}

    def start_workflow(
        self,
        workflow_name: str,
        workflow_input: dict[str, Any],
        task_queue: str = "devops-companion",
        timeout_seconds: int = 3600,
    ) -> dict[str, Any]:
        """Start a new workflow execution."""
        _sim_temporal_delay()
        wf_id = _id("devops-companion")
        run_id = _id("run")
        now = datetime.now(timezone.utc)

        state = {
            "workflow_id": wf_id,
            "run_id": run_id,
            "workflow_name": workflow_name,
            "status": "RUNNING",
            "task_queue": task_queue,
            "input": workflow_input,
            "started_at": now.isoformat(),
            "activities_completed": [],
            "activities_remaining": [a["name"] for a in PIPELINE_ACTIVITIES],
            "current_activity": PIPELINE_ACTIVITIES[0]["name"],
            "checkpoint_count": 0,
            "signals_received": [],
            "waiting_for_signal": False,
            "timeout_seconds": timeout_seconds,
            "saga_log": [],
        }
        self._workflows[wf_id] = state

        return {
            "workflow_id": wf_id,
            "run_id": run_id,
            "status": "RUNNING",
            "task_queue": task_queue,
            "started_at": now.isoformat(),
            "mock_mode": True,
        }

    def execute_activity(
        self,
        workflow_id: str,
        activity_name: str,
        activity_input: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute a single activity and record a checkpoint."""
        _sim_temporal_delay()
        state = self._workflows.get(workflow_id)
        if not state:
            return {"error": f"Workflow {workflow_id} not found"}

        if state["waiting_for_signal"]:
            return {
                "error": "Workflow is paused waiting for signal",
                "signal_name": "approve_deployment",
            }

        state["activities_completed"].append(activity_name)
        if activity_name in state["activities_remaining"]:
            state["activities_remaining"].remove(activity_name)
        state["checkpoint_count"] += 1

        if state["activities_remaining"]:
            state["current_activity"] = state["activities_remaining"][0]
        else:
            state["current_activity"] = None
            state["status"] = "COMPLETED"

        activity_meta = next(
            (a for a in PIPELINE_ACTIVITIES if a["name"] == activity_name),
            {"typical_duration_s": 5, "uses_bedrock": False},
        )

        return {
            "workflow_id": workflow_id,
            "activity": activity_name,
            "status": "COMPLETED",
            "checkpoint_number": state["checkpoint_count"],
            "duration_seconds": activity_meta["typical_duration_s"],
            "used_bedrock": activity_meta["uses_bedrock"],
            "activities_remaining": len(state["activities_remaining"]),
            "mock_mode": True,
        }

    def pause_for_signal(
        self,
        workflow_id: str,
        signal_name: str = "approve_deployment",
    ) -> dict[str, Any]:
        """Pause workflow to wait for an external signal (human approval).

        In Temporal, signals are addressed by workflow ID — no tokens needed.
        The external system calls client.get_workflow_handle(workflow_id).signal().
        """
        _sim_temporal_delay()
        state = self._workflows.get(workflow_id)
        if not state:
            return {"error": f"Workflow {workflow_id} not found"}

        state["waiting_for_signal"] = True
        state["status"] = "WAITING_FOR_SIGNAL"

        return {
            "workflow_id": workflow_id,
            "run_id": state["run_id"],
            "status": "WAITING_FOR_SIGNAL",
            "signal_name": signal_name,
            "paused_at": _ts(),
            "checkpoint_count": state["checkpoint_count"],
            "activities_completed": state["activities_completed"],
            "signal_target": f"client.get_workflow_handle('{workflow_id}').signal('{signal_name}', ...)",
            "mock_mode": True,
        }

    def signal_workflow(
        self,
        workflow_id: str,
        signal_name: str,
        signal_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Send a signal to a waiting workflow (e.g., approval decision)."""
        _sim_temporal_delay()
        state = self._workflows.get(workflow_id)
        if not state:
            return {"error": f"Workflow {workflow_id} not found"}

        state["waiting_for_signal"] = False
        state["status"] = "RUNNING"
        state["signals_received"].append({
            "signal_name": signal_name,
            "signal_data": signal_data or {},
            "received_at": _ts(),
        })

        return {
            "workflow_id": workflow_id,
            "signal_name": signal_name,
            "signal_delivered": True,
            "signal_data": signal_data or {},
            "workflow_status": "RUNNING",
            "delivered_at": _ts(),
            "mock_mode": True,
        }

    def query_workflow(
        self,
        workflow_id: str,
        query_name: str = "current_state",
    ) -> dict[str, Any]:
        """Query current workflow state (non-mutating)."""
        state = self._workflows.get(workflow_id)
        if not state:
            return {"error": f"Workflow {workflow_id} not found"}

        now = datetime.now(timezone.utc)
        started = datetime.fromisoformat(state["started_at"])
        elapsed = (now - started).total_seconds()

        return {
            "workflow_id": workflow_id,
            "status": state["status"],
            "current_activity": state["current_activity"],
            "checkpoint_count": state["checkpoint_count"],
            "activities_completed": state["activities_completed"],
            "activities_remaining": state["activities_remaining"],
            "waiting_for_signal": state["waiting_for_signal"],
            "elapsed_seconds": int(elapsed),
            "signals_received": len(state["signals_received"]),
            "mock_mode": True,
        }

    def get_workflow_history(
        self,
        workflow_id: str,
    ) -> dict[str, Any]:
        """Get full event history for a workflow execution."""
        state = self._workflows.get(workflow_id)
        if not state:
            return {"error": f"Workflow {workflow_id} not found"}

        started = datetime.fromisoformat(state["started_at"])
        events = [
            {
                "event_id": 1,
                "event_type": "WorkflowExecutionStarted",
                "timestamp": state["started_at"],
                "details": {"task_queue": state["task_queue"]},
            }
        ]

        offset = timedelta(seconds=1)
        for i, activity in enumerate(state["activities_completed"], start=1):
            meta = next(
                (a for a in PIPELINE_ACTIVITIES if a["name"] == activity),
                {"typical_duration_s": 5},
            )
            events.append({
                "event_id": i * 2,
                "event_type": "ActivityTaskScheduled",
                "timestamp": (started + offset).isoformat(),
                "details": {"activity": activity},
            })
            offset += timedelta(seconds=meta["typical_duration_s"])
            events.append({
                "event_id": i * 2 + 1,
                "event_type": "ActivityTaskCompleted",
                "timestamp": (started + offset).isoformat(),
                "details": {"activity": activity, "checkpoint": i},
            })

        for sig in state["signals_received"]:
            events.append({
                "event_id": len(events) + 1,
                "event_type": "WorkflowSignalReceived",
                "timestamp": sig["received_at"],
                "details": {"signal": sig["signal_name"], "data": sig["signal_data"]},
            })

        return {
            "workflow_id": workflow_id,
            "run_id": state["run_id"],
            "events": events,
            "total_events": len(events),
            "mock_mode": True,
        }

    def simulate_crash_and_replay(
        self,
        workflow_id: str,
        crash_after_activity: str,
    ) -> dict[str, Any]:
        """Simulate a worker crash and Temporal's replay recovery.

        Shows which activities are replayed (skipped) vs re-executed.
        """
        state = self._workflows.get(workflow_id)
        if not state:
            return {"error": f"Workflow {workflow_id} not found"}

        completed = state["activities_completed"]
        if crash_after_activity not in completed:
            return {
                "error": f"Activity '{crash_after_activity}' has not completed yet",
                "completed": completed,
            }

        crash_idx = completed.index(crash_after_activity)
        replayed = completed[: crash_idx + 1]
        remaining = [
            a["name"] for a in PIPELINE_ACTIVITIES
            if a["name"] not in replayed
        ]

        return {
            "workflow_id": workflow_id,
            "crash_point": crash_after_activity,
            "recovery": "REPLAY",
            "replayed_activities": replayed,
            "skipped_re_execution": True,
            "resumed_from": remaining[0] if remaining else None,
            "remaining_activities": remaining,
            "checkpoint_count": len(replayed),
            "message": (
                f"Worker crashed after '{crash_after_activity}'. "
                f"Temporal replayed {len(replayed)} activities (skipped re-execution). "
                f"Resuming from '{remaining[0]}'." if remaining else "Workflow already complete."
            ),
            "mock_mode": True,
        }

    def execute_saga_step(
        self,
        workflow_id: str,
        activity_name: str,
        compensation_name: str,
        activity_input: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute an activity and register its compensation in the saga log."""
        state = self._workflows.get(workflow_id)
        if not state:
            return {"error": f"Workflow {workflow_id} not found"}

        state["saga_log"].append({
            "activity": activity_name,
            "compensation": compensation_name,
            "completed_at": _ts(),
        })

        result = self.execute_activity(workflow_id, activity_name, activity_input)
        result["compensation_registered"] = compensation_name
        result["saga_step"] = len(state["saga_log"])
        return result

    def trigger_saga_compensation(
        self,
        workflow_id: str,
        failure_at: str,
    ) -> dict[str, Any]:
        """Simulate failure at a step and execute compensations in reverse order."""
        state = self._workflows.get(workflow_id)
        if not state:
            return {"error": f"Workflow {workflow_id} not found"}

        saga_log = state["saga_log"]
        state["status"] = "COMPENSATING"

        compensations_executed = []
        for entry in reversed(saga_log):
            compensations_executed.append({
                "compensation": entry["compensation"],
                "for_activity": entry["activity"],
                "status": "COMPLETED",
                "executed_at": _ts(),
            })

        state["status"] = "COMPENSATED"

        return {
            "workflow_id": workflow_id,
            "failure_at": failure_at,
            "saga_steps_completed": len(saga_log),
            "compensations_executed": compensations_executed,
            "compensation_order": [c["compensation"] for c in compensations_executed],
            "final_status": "COMPENSATED",
            "message": (
                f"Activity '{failure_at}' failed. "
                f"Executed {len(compensations_executed)} compensations in reverse order."
            ),
            "mock_mode": True,
        }

    def get_worker_info(self) -> dict[str, Any]:
        """Return mock worker fleet status."""
        return {
            "task_queue": "devops-companion",
            "workers": [
                {"identity": "worker-fargate-1a2b3c", "status": "POLLING", "last_heartbeat": _ts()},
                {"identity": "worker-fargate-4d5e6f", "status": "POLLING", "last_heartbeat": _ts()},
                {"identity": "worker-fargate-7g8h9i", "status": "EXECUTING", "last_heartbeat": _ts()},
                {"identity": "worker-fargate-0j1k2l", "status": "POLLING", "last_heartbeat": _ts()},
            ],
            "max_concurrent_activities": 5,
            "max_concurrent_workflow_tasks": 10,
            "schedule_to_start_latency_ms": 850,
            "active_workflows": len([w for w in self._workflows.values() if w["status"] == "RUNNING"]),
            "mock_mode": True,
        }


# Singleton for the demo
_mock_client: MockTemporalClient | None = None


def get_mock_temporal_client() -> MockTemporalClient:
    """Get or create the singleton mock Temporal client."""
    global _mock_client
    if _mock_client is None:
        _mock_client = MockTemporalClient()
    return _mock_client
