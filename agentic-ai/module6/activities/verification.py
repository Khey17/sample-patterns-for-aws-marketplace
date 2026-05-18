"""
module6/activities/verification.py
====================================
Static security scanning, compliance checking, and smoke test activities.

These are deterministic checks (cdk-nag, cfn-guard, policy rules) — no
LLM call needed. They return structured findings directly.
"""

from __future__ import annotations

import os
from typing import Any

from module6.activities._endpoints import sim_work_delay
from module6.mock.aws_mocks import MOCK_SECURITY_SCAN, MOCK_COMPLIANCE_CHECK


def static_security_scan(cdk_output: dict[str, Any]) -> dict[str, Any]:
    """Static analysis of generated CDK code for security issues.

    Evaluates CDK/CloudFormation templates against security rules
    (cdk-nag, cfn-guard) without deploying any infrastructure.
    Returns findings categorized by severity.
    """
    sim_work_delay()
    stacks_scanned = cdk_output.get("stacks_generated", 5)
    scan = dict(MOCK_SECURITY_SCAN)

    return {
        "activity": "static_security_scan",
        "stacks_scanned": stacks_scanned,
        "findings": scan["findings"],
        "summary": {
            "critical": scan["critical"],
            "high": scan["high"],
            "medium": scan["medium"],
            "low": scan["low"],
            "info": scan["info"],
        },
        "passed": scan["passed"],
        "blocking": scan["critical"] > 0,
        "mock_mode": True,
    }


def compliance_check(cdk_output: dict[str, Any]) -> dict[str, Any]:
    """Check generated CDK code against organizational policies.

    Evaluates: required resource tags, naming conventions,
    encryption-at-rest, and public endpoint exposure.
    """
    sim_work_delay()
    stacks_checked = cdk_output.get("stacks_generated", 5)
    result = dict(MOCK_COMPLIANCE_CHECK)

    severity_counts = {"medium": 0, "low": 0, "info": 0}
    for f in result["findings"]:
        sev = f["severity"].lower()
        if sev in severity_counts:
            severity_counts[sev] += 1

    return {
        "activity": "compliance_check",
        "stacks_checked": stacks_checked,
        "findings": result["findings"],
        "categories_checked": result["categories_checked"],
        "summary": severity_counts,
        "passed": result["passed"],
        "blocking": result["blocking"],
        "mock_mode": True,
    }


def smoke_tests(deployment: dict[str, Any]) -> dict[str, Any]:
    """Run post-deployment smoke tests against the deployed service.

    Verifies:
    - Health endpoint responds 200
    - Response time is within SLA
    - No error logs in first 30 seconds
    """
    sim_work_delay()
    service_name = deployment.get("service_name", "api-service")
    tests = [
        {"name": "health_endpoint", "status": "passed", "response_ms": 45},
        {"name": "response_time_sla", "status": "passed", "p99_ms": 180, "sla_ms": 500},
        {"name": "error_log_check", "status": "passed", "errors_found": 0},
        {"name": "connectivity", "status": "passed", "endpoints_reachable": 3},
    ]

    return {
        "activity": "smoke_tests",
        "service": service_name,
        "tests_run": len(tests),
        "tests_passed": len([t for t in tests if t["status"] == "passed"]),
        "tests_failed": len([t for t in tests if t["status"] == "failed"]),
        "results": tests,
        "overall": "PASSED",
        "mock_mode": True,
    }
