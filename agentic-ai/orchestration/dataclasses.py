"""
orchestration/dataclasses.py
=============================
Typed input/output dataclasses for workflow and activities.

All fields must be JSON-serializable (Temporal SDK requirement).
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class WorkflowInput:
    repo_path: str
    region: str = "us-east-1"
    environment: str = "dev"
    demo_mode: bool = False


@dataclass
class AnalysisResult:
    repo_path: str
    region: str
    analysis: str
    frameworks_detected: list[str] = field(default_factory=list)
    languages: list[str] = field(default_factory=list)
    aws_services_needed: list[str] = field(default_factory=list)
    estimated_stacks: int = 0
    source: str = "mock"


@dataclass
class DependencyMapping:
    total_dependencies: int
    mappings: list[dict] = field(default_factory=list)
    deployment_target: str = "ECS Fargate"
    networking: str = "VPC with private subnets"


@dataclass
class CdkResult:
    stacks_generated: int
    stacks: list[dict] = field(default_factory=list)
    total_resources: int = 0
    language: str = "TypeScript"
    cdk_version: str = "2.x"
    code_preview: str = ""
    syntax_valid: bool = True
    estimated_monthly_cost: str = "$450-$650"
    source: str = "mock"


@dataclass
class SecurityScanResult:
    stacks_scanned: int
    findings: list[dict] = field(default_factory=list)
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    info: int = 0
    passed: bool = True
    blocking: bool = False


@dataclass
class ComplianceResult:
    stacks_checked: int
    findings: list[dict] = field(default_factory=list)
    categories_checked: list[str] = field(default_factory=list)
    medium: int = 0
    low: int = 0
    info_count: int = 0
    passed: bool = True
    blocking: bool = False


@dataclass
class DeploymentResult:
    cluster: str = "devops-companion"
    service_name: str = "api-service"
    task_definition: str = "devops-companion-api:3"
    status: str = "DEPLOYED"
    running_count: int = 2
    desired_count: int = 2
    deployment_duration_seconds: int = 50


@dataclass
class SmokeTestResult:
    service: str = "api-service"
    tests_run: int = 4
    tests_passed: int = 4
    tests_failed: int = 0
    overall: str = "PASSED"
    results: list[dict] = field(default_factory=list)


@dataclass
class ObservabilityResult:
    service: str = "api-service"
    alarms_configured: int = 3
    alarms: list[dict] = field(default_factory=list)
    otlp_export_enabled: bool = True


@dataclass
class SagaInput:
    cdk_stacks: int = 5
    force_failure_at: str = ""


@dataclass
class SagaResult:
    status: str
    steps_completed: int = 0
    compensations_executed: list[str] = field(default_factory=list)
    failure_at: str = ""


@dataclass
class ApprovalDecision:
    approved: bool
    reviewer: str
    comments: str = ""


@dataclass
class WorkflowResult:
    status: str
    workflow_id: str = ""
    analysis: AnalysisResult | None = None
    cdk: CdkResult | None = None
    security_scan: SecurityScanResult | None = None
    compliance: ComplianceResult | None = None
    deployment: DeploymentResult | None = None
    smoke_tests: SmokeTestResult | None = None
    observability: ObservabilityResult | None = None
    approval: ApprovalDecision | None = None
    error: str = ""
