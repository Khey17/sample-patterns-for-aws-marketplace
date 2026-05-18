"""
module6/mock/aws_mocks.py
==========================
Mock AWS services for Module 6: Bedrock, ECS, EventBridge, CloudWatch.

Controlled by AGENT_MOCK_MODE env var (default: "true"). When false and
credentials are available, real boto3 calls would be made.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta
from typing import Any


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str = "id") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


# ---------------------------------------------------------------------------
# Bedrock mocks
# ---------------------------------------------------------------------------

MOCK_ANALYSIS_RESPONSE = (
    "Repository contains a Node.js API (Express) and a Python worker service. "
    "Dependencies: PostgreSQL (RDS), Redis (ElastiCache), S3 for assets. "
    "Deployment target: ECS Fargate with ALB. Estimated 5 CDK stacks needed: "
    "VpcStack, RdsStack, ElastiCacheStack, EcsApiStack, EcsWorkerStack."
)

MOCK_CDK_RESPONSE = """import * as cdk from 'aws-cdk-lib';
import * as ecs from 'aws-cdk-lib/aws-ecs';
import * as ec2 from 'aws-cdk-lib/aws-ec2';

export class EcsApiStack extends cdk.Stack {
  constructor(scope: cdk.App, id: string, props?: cdk.StackProps) {
    super(scope, id, props);
    const cluster = new ecs.Cluster(this, 'ApiCluster', {
      vpc: ec2.Vpc.fromLookup(this, 'Vpc', { isDefault: false }),
    });
    const taskDef = new ecs.FargateTaskDefinition(this, 'ApiTask', {
      memoryLimitMiB: 512, cpu: 256,
    });
    taskDef.addContainer('api', {
      image: ecs.ContainerImage.fromRegistry('app/api:latest'),
      portMappings: [{ containerPort: 3000 }],
    });
  }
}"""

MOCK_SECURITY_SCAN = {
    "findings": [
        {"severity": "LOW", "rule": "AwsSolutions-ECS4", "message": "Enable ECS Exec logging"},
        {"severity": "INFO", "rule": "AwsSolutions-VPC7", "message": "Consider VPC flow logs"},
    ],
    "critical": 0,
    "high": 0,
    "medium": 0,
    "low": 1,
    "info": 1,
    "passed": True,
}

MOCK_COMPLIANCE_CHECK = {
    "findings": [
        {"category": "TAGGING", "severity": "MEDIUM", "rule": "OrgPolicy-Tags-001",
         "message": "Missing required tag 'cost-center' on ECS service"},
        {"category": "NAMING", "severity": "LOW", "rule": "OrgPolicy-Naming-002",
         "message": "Resource name 'MyStack-Bucket1' does not follow kebab-case convention"},
        {"category": "ENCRYPTION", "severity": "INFO", "rule": "OrgPolicy-Encrypt-001",
         "message": "All storage resources have encryption-at-rest enabled"},
    ],
    "categories_checked": ["tagging", "naming", "encryption", "public_exposure"],
    "passed": True,
    "blocking": False,
}


def mock_invoke_bedrock(prompt: str, activity_type: str = "analysis") -> str:
    """Return mock Bedrock response based on activity type."""
    if activity_type == "analysis":
        return MOCK_ANALYSIS_RESPONSE
    elif activity_type == "cdk_generation":
        return MOCK_CDK_RESPONSE
    elif activity_type == "static_security_scan":
        return f"Static security scan complete. {MOCK_SECURITY_SCAN['critical']} critical, {MOCK_SECURITY_SCAN['low']} low findings."
    elif activity_type == "compliance_check":
        return f"Compliance check complete. {len(MOCK_COMPLIANCE_CHECK['findings'])} findings across {len(MOCK_COMPLIANCE_CHECK['categories_checked'])} categories."
    return f"Mock Bedrock response for: {prompt[:100]}"


# ---------------------------------------------------------------------------
# ECS mocks
# ---------------------------------------------------------------------------

def mock_create_ecs_service(
    cluster: str,
    service_name: str,
    task_definition: str,
) -> dict[str, Any]:
    """Mock creating an ECS Fargate service."""
    return {
        "service": {
            "serviceArn": f"arn:aws:ecs:us-east-1:123456789012:service/{cluster}/{service_name}",
            "serviceName": service_name,
            "clusterArn": f"arn:aws:ecs:us-east-1:123456789012:cluster/{cluster}",
            "taskDefinition": task_definition,
            "desiredCount": 2,
            "runningCount": 0,
            "status": "ACTIVE",
            "launchType": "FARGATE",
            "createdAt": _ts(),
        }
    }


def mock_describe_ecs_services(
    cluster: str,
    services: list[str],
) -> dict[str, Any]:
    """Mock describing ECS services (for health checks)."""
    result = []
    for svc in services:
        result.append({
            "serviceArn": f"arn:aws:ecs:us-east-1:123456789012:service/{cluster}/{svc}",
            "serviceName": svc,
            "status": "ACTIVE",
            "desiredCount": 2,
            "runningCount": 2,
            "pendingCount": 0,
            "launchType": "FARGATE",
            "deployments": [
                {
                    "id": _id("deployment"),
                    "status": "PRIMARY",
                    "desiredCount": 2,
                    "runningCount": 2,
                    "rolloutState": "COMPLETED",
                }
            ],
        })
    return {"services": result, "failures": []}


def mock_ecs_wait_stable(cluster: str, service_name: str) -> dict[str, Any]:
    """Mock waiting for ECS service to reach steady state."""
    return {
        "cluster": cluster,
        "service": service_name,
        "status": "STABLE",
        "runningCount": 2,
        "desiredCount": 2,
        "wait_time_seconds": 45,
    }


# ---------------------------------------------------------------------------
# EventBridge mocks
# ---------------------------------------------------------------------------

def mock_put_eventbridge_rule(
    name: str,
    event_pattern: dict[str, Any] | None = None,
    schedule: str | None = None,
) -> dict[str, Any]:
    """Mock creating an EventBridge rule."""
    return {
        "RuleArn": f"arn:aws:events:us-east-1:123456789012:rule/{name}",
        "Name": name,
        "EventPattern": event_pattern,
        "ScheduleExpression": schedule,
        "State": "ENABLED",
    }


def mock_eventbridge_trigger(
    rule_name: str,
    detail_type: str,
    detail: dict[str, Any],
) -> dict[str, Any]:
    """Mock an EventBridge event triggering a workflow start."""
    return {
        "event_id": _id("evt"),
        "rule": rule_name,
        "detail_type": detail_type,
        "detail": detail,
        "time": _ts(),
        "action": "start_workflow",
        "target": "devops-companion-starter-lambda",
    }


# ---------------------------------------------------------------------------
# CloudWatch mocks
# ---------------------------------------------------------------------------

def mock_cloudwatch_alarms() -> list[dict[str, Any]]:
    """Mock CloudWatch alarms for Temporal worker fleet."""
    return [
        {
            "AlarmName": "TemporalWorker-HighCPU",
            "MetricName": "CPUUtilization",
            "Namespace": "AWS/ECS",
            "Threshold": 80.0,
            "StateValue": "OK",
            "ComparisonOperator": "GreaterThanThreshold",
        },
        {
            "AlarmName": "TemporalWorker-BacklogGrowing",
            "MetricName": "schedule_to_start_latency_ms",
            "Namespace": "Temporal/Workers",
            "Threshold": 30000.0,
            "StateValue": "OK",
            "ComparisonOperator": "GreaterThanThreshold",
        },
        {
            "AlarmName": "DevOpsCompanion-WorkflowFailures",
            "MetricName": "workflow_failed_count",
            "Namespace": "Temporal/Workflows",
            "Threshold": 5.0,
            "StateValue": "OK",
            "ComparisonOperator": "GreaterThanThreshold",
        },
    ]


def mock_cloudwatch_metrics() -> dict[str, Any]:
    """Mock CloudWatch metric data for the worker fleet."""
    return {
        "WorkerCPUUtilization": 42.3,
        "WorkerMemoryUtilization": 61.7,
        "ActiveWorkflows": 3,
        "ScheduleToStartLatencyP99_ms": 1200,
        "ActivitySuccessRate": 0.97,
        "WorkflowCompletionRate": 0.94,
    }
