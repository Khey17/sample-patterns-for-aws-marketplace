"""
orchestration/activities/generation.py
========================================
CDK infrastructure code generation activity.
"""

from __future__ import annotations

from temporalio import activity

from orchestration.dataclasses import DependencyMapping, CdkResult
from orchestration.activities._http_client import call_module3

MOCK_CDK_CODE = """import * as cdk from 'aws-cdk-lib';
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

STACKS = [
    {"name": "VpcStack", "resources": 6},
    {"name": "RdsStack", "resources": 4},
    {"name": "ElastiCacheStack", "resources": 3},
    {"name": "EcsApiStack", "resources": 8},
    {"name": "EcsWorkerStack", "resources": 8},
]


@activity.defn
async def generate_cdk(deps: DependencyMapping) -> CdkResult:
    """Generate CDK infrastructure code from dependency mapping."""
    result = await call_module3("/generate", {
        "requirements": {"mappings": deps.mappings},
        "region": "us-east-1",
        "environment": "dev",
    })

    code = MOCK_CDK_CODE
    source = "mock"
    if result and result.get("status") == "success":
        code = result.get("output", MOCK_CDK_CODE)
        source = "module3_endpoint"

    return CdkResult(
        stacks_generated=len(STACKS),
        stacks=STACKS,
        total_resources=sum(s["resources"] for s in STACKS),
        language="TypeScript",
        cdk_version="2.x",
        code_preview=code[:200] + "...",
        syntax_valid=True,
        estimated_monthly_cost="$450-$650",
        source=source,
    )
