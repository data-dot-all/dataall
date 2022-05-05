#!/usr/bin/env python3


import os

import boto3
from aws_cdk import App, Aspects, Environment
from cdk_nag import AwsSolutionsChecks, NagPackSuppression, NagSuppressions
from stacks.cdk_nag_exclusions import PIPELINE_STACK_CDK_NAG_EXCLUSIONS
from stacks.pipeline import PipelineStack

account_id = boto3.client("sts").get_caller_identity().get("Account") or os.getenv("CDK_DEFAULT_ACCOUNT")
app = App()

git_branch = app.node.try_get_context("git_branch") or "main"

cdk_pipeline_region = app.node.try_get_context("tooling_region") or os.getenv("CDK_DEFAULT_REGION")

target_envs = app.node.try_get_context("DeploymentEnvironments") or [
    {"envname": "dev", "account": account_id, "region": "eu-west-1"}
]

env = Environment(account=account_id, region=cdk_pipeline_region)

resource_prefix = app.node.try_get_context("resource_prefix") or "dataall"

pipeline = PipelineStack(
    app,
    "{resource_prefix}-{git_branch}-cicd-stack".format(resource_prefix=resource_prefix, git_branch=git_branch),
    env=env,
    target_envs=target_envs,
    git_branch=git_branch,
    resource_prefix=resource_prefix,
)

Aspects.of(app).add(AwsSolutionsChecks(reports=True, verbose=False))

NagSuppressions.add_stack_suppressions(
    pipeline,
    suppressions=[
        NagPackSuppression(id=rule_suppressed["id"], reason=rule_suppressed["reason"])
        for rule_suppressed in PIPELINE_STACK_CDK_NAG_EXCLUSIONS
    ],
    apply_to_nested_stacks=True,
)

app.synth()
