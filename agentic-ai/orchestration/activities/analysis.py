"""
orchestration/activities/analysis.py
======================================
Repository analysis and dependency mapping activities.
"""

from __future__ import annotations

from temporalio import activity

from orchestration.dataclasses import WorkflowInput, AnalysisResult, DependencyMapping
from orchestration.activities._http_client import call_module2

MOCK_ANALYSIS = (
    "Repository contains a Node.js API (Express) and a Python worker service. "
    "Dependencies: PostgreSQL (RDS), Redis (ElastiCache), S3 for assets. "
    "Deployment target: ECS Fargate with ALB. Estimated 5 CDK stacks needed: "
    "VpcStack, RdsStack, ElastiCacheStack, EcsApiStack, EcsWorkerStack."
)


@activity.defn
async def analyze_repository(input: WorkflowInput) -> AnalysisResult:
    """Analyze a code repository via Module 2 endpoint."""
    result = await call_module2("/analyze", {"repo_path": input.repo_path})

    if result and "error" not in result:
        return AnalysisResult(
            repo_path=input.repo_path,
            region=input.region,
            analysis=result.get("analysis", MOCK_ANALYSIS),
            frameworks_detected=["express", "flask"],
            languages=["typescript", "python"],
            aws_services_needed=["ECS", "RDS", "ElastiCache", "S3", "ALB"],
            estimated_stacks=5,
            source="module2_endpoint",
        )

    return AnalysisResult(
        repo_path=input.repo_path,
        region=input.region,
        analysis=MOCK_ANALYSIS,
        frameworks_detected=["express", "flask"],
        languages=["typescript", "python"],
        aws_services_needed=["ECS", "RDS", "ElastiCache", "S3", "ALB"],
        estimated_stacks=5,
        source="mock",
    )


@activity.defn
async def map_dependencies(analysis: AnalysisResult) -> DependencyMapping:
    """Map detected dependencies to AWS service configurations (deterministic)."""
    services = analysis.aws_services_needed
    mappings = []
    for svc in services:
        mappings.append({
            "service": svc,
            "construct": f"aws-cdk-lib/aws-{svc.lower()}",
            "configuration": {
                "high_availability": True,
                "multi_az": svc in ("RDS", "ElastiCache"),
                "encryption_at_rest": True,
            },
        })

    return DependencyMapping(
        total_dependencies=len(mappings),
        mappings=mappings,
        deployment_target="ECS Fargate",
        networking="VPC with private subnets",
    )
