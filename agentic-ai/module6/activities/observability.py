"""
module6/activities/observability.py
=====================================
Observability setup and trace retrieval activities.

Configures CloudWatch alarms for the deployed service and retrieves
OpenTelemetry traces that correlate Temporal workflow events with
Bedrock call latency and ECS task health.
"""

from __future__ import annotations

import os
import random
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any

from module6.activities._endpoints import sim_work_delay
from module6.mock.aws_mocks import mock_cloudwatch_alarms, mock_cloudwatch_metrics


def setup_observability(deployment: dict[str, Any]) -> dict[str, Any]:
    """Configure CloudWatch alarms and Datadog dashboards for the deployment."""
    mock_mode = os.getenv("AGENT_MOCK_MODE", "true").lower() == "true"

    sim_work_delay()
    service = deployment.get("service_name", "api-service")
    alarms_configured = [
        {"name": f"{service}-HighCPU", "metric": "CPUUtilization", "threshold": 80},
        {"name": f"{service}-ErrorRate", "metric": "5XXError", "threshold": 5},
        {"name": f"{service}-Latency", "metric": "TargetResponseTime", "threshold": 2.0},
    ]

    return {
        "activity": "setup_observability",
        "service": service,
        "alarms_configured": len(alarms_configured),
        "alarms": alarms_configured,
        "datadog_dashboard": f"https://app.datadoghq.com/dashboard/devops-companion-{service}",
        "otlp_export_enabled": True,
        "mock_mode": mock_mode,
    }


def get_workflow_traces(workflow_id: str) -> dict[str, Any]:
    """Retrieve end-to-end traces for a workflow execution.

    Correlates Temporal workflow spans, Bedrock activity latency,
    ECS deployment timing, and CloudWatch metrics into one view.
    This is what lands in Datadog APM as a distributed trace.
    """
    mock_mode = os.getenv("AGENT_MOCK_MODE", "true").lower() == "true"
    now = datetime.now(timezone.utc)
    trace_id = f"1-{uuid.uuid4().hex[:8]}-{uuid.uuid4().hex[:24]}"

    spans = [
        {
            "span_id": uuid.uuid4().hex[:16],
            "operation": "analyze_repository",
            "service": "bedrock-activity",
            "duration_ms": random.randint(800, 1800),
            "status": "ok",
            "attributes": {"bedrock.model": "claude-sonnet-4-6", "bedrock.tokens": 847},
        },
        {
            "span_id": uuid.uuid4().hex[:16],
            "operation": "map_dependencies",
            "service": "deterministic-activity",
            "duration_ms": random.randint(50, 200),
            "status": "ok",
        },
        {
            "span_id": uuid.uuid4().hex[:16],
            "operation": "generate_cdk",
            "service": "bedrock-activity",
            "duration_ms": random.randint(1800, 3200),
            "status": "ok",
            "attributes": {"bedrock.model": "claude-sonnet-4-6", "bedrock.tokens": 2104},
        },
        {
            "span_id": uuid.uuid4().hex[:16],
            "operation": "wait_for_signal:approve_deployment",
            "service": "temporal-workflow",
            "duration_ms": random.randint(120000, 300000),
            "status": "ok",
            "attributes": {"signal.wait_duration": "3m"},
        },
        {
            "span_id": uuid.uuid4().hex[:16],
            "operation": "deploy_to_ecs",
            "service": "ecs-activity",
            "duration_ms": random.randint(35000, 60000),
            "status": "ok",
            "attributes": {"ecs.cluster": "devops-companion", "ecs.service": "api-service"},
        },
        {
            "span_id": uuid.uuid4().hex[:16],
            "operation": "smoke_tests",
            "service": "verification-activity",
            "duration_ms": random.randint(8000, 15000),
            "status": "ok",
        },
    ]
    total_ms = sum(s["duration_ms"] for s in spans)
    spans.insert(0, {
        "span_id": uuid.uuid4().hex[:16],
        "operation": "DevOpsCompanionWorkflow.run",
        "service": "temporal-workflow",
        "duration_ms": total_ms,
        "status": "ok",
    })

    cw_metrics = mock_cloudwatch_metrics()
    cw_alarms = mock_cloudwatch_alarms()

    return {
        "trace_id": trace_id,
        "workflow_id": workflow_id,
        "spans": spans,
        "total_spans": len(spans),
        "total_duration_ms": total_ms,
        "bedrock_calls": len([s for s in spans if "bedrock" in s["service"]]),
        "bedrock_total_ms": sum(
            s["duration_ms"] for s in spans if "bedrock" in s["service"]
        ),
        "cloudwatch": {
            "alarms": cw_alarms,
            "metrics": cw_metrics,
        },
        "datadog_trace_url": "https://datadoghq.com/apm/entity/service%3Adevops-companion#traces",
        "otlp_exporter": "opentelemetry-exporter-otlp-grpc",
        "temporal_interceptor": "TracingInterceptor",
        "mock_mode": mock_mode,
    }


def get_temporal_cloud_metrics() -> dict[str, Any]:
    """Retrieve Temporal Cloud metrics as they would appear in Datadog.

    Temporal Cloud exports metrics via a Prometheus endpoint. The Datadog
    Agent scrapes these and makes them available as custom metrics.
    """
    return {
        "source": "temporal_cloud_prometheus",
        "metrics": {
            "temporal.workflow.completed": 142,
            "temporal.workflow.failed": 4,
            "temporal.workflow.active": 3,
            "temporal.activity.schedule_to_start_latency_ms_p99": 1200,
            "temporal.activity.execution_latency_ms_p99": 3400,
            "temporal.worker.task_slots_available": 17,
            "temporal.namespace.action_count": 12847,
        },
        "namespace": "devops-companion.tmprl.cloud",
        "mock_mode": True,
    }
