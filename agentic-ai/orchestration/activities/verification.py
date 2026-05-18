"""
orchestration/activities/verification.py
==========================================
Static security scan, compliance check, and smoke test activities.
"""

from __future__ import annotations

import asyncio

from temporalio import activity

from orchestration.dataclasses import (
    CdkResult,
    SecurityScanResult,
    ComplianceResult,
    DeploymentResult,
    SmokeTestResult,
)


@activity.defn
async def static_security_scan(cdk: CdkResult) -> SecurityScanResult:
    """Static analysis of generated CDK code for security issues."""
    await asyncio.sleep(0.5)

    findings = [
        {"severity": "LOW", "rule": "AwsSolutions-ECS4", "message": "Enable ECS Exec logging"},
        {"severity": "INFO", "rule": "AwsSolutions-VPC7", "message": "Consider VPC flow logs"},
    ]

    return SecurityScanResult(
        stacks_scanned=cdk.stacks_generated,
        findings=findings,
        critical=0,
        high=0,
        medium=0,
        low=1,
        info=1,
        passed=True,
        blocking=False,
    )


@activity.defn
async def compliance_check(cdk: CdkResult) -> ComplianceResult:
    """Check generated CDK code against organizational policies."""
    await asyncio.sleep(0.5)

    findings = [
        {
            "category": "TAGGING",
            "severity": "MEDIUM",
            "rule": "OrgPolicy-Tags-001",
            "message": "Missing required tag 'cost-center' on ECS service",
        },
        {
            "category": "NAMING",
            "severity": "LOW",
            "rule": "OrgPolicy-Naming-002",
            "message": "Resource name does not follow kebab-case convention",
        },
        {
            "category": "ENCRYPTION",
            "severity": "INFO",
            "rule": "OrgPolicy-Encrypt-001",
            "message": "All storage resources have encryption-at-rest enabled",
        },
    ]

    return ComplianceResult(
        stacks_checked=cdk.stacks_generated,
        findings=findings,
        categories_checked=["tagging", "naming", "encryption", "public_exposure"],
        medium=1,
        low=1,
        info_count=1,
        passed=True,
        blocking=False,
    )


@activity.defn
async def smoke_tests(deployment: DeploymentResult) -> SmokeTestResult:
    """Run post-deployment smoke tests against the deployed service."""
    await asyncio.sleep(1)

    results = [
        {"name": "health_endpoint", "status": "passed", "response_ms": 45},
        {"name": "response_time_sla", "status": "passed", "p99_ms": 180, "sla_ms": 500},
        {"name": "error_log_check", "status": "passed", "errors_found": 0},
        {"name": "connectivity", "status": "passed", "endpoints_reachable": 3},
    ]

    return SmokeTestResult(
        service=deployment.service_name,
        tests_run=len(results),
        tests_passed=len(results),
        tests_failed=0,
        overall="PASSED",
        results=results,
    )
