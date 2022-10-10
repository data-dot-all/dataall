#!/usr/bin/env python3

import json
import os
import re

import boto3
from aws_cdk import aws_ssm as ssm
from aws_cdk import App, Environment, Aspects
from cdk_nag import AwsSolutionsChecks, NagSuppressions, NagPackSuppression

from stacks.cdk_nag_exclusions import PIPELINE_STACK_CDK_NAG_EXCLUSIONS
from stacks.pipeline import PipelineStack


def get_cdk_json_from_ssm():
    ssmc = boto3.client('ssm')

    try:
        return ssmc.get_parameter(Name="/dataall/v1m1m0/cdkjson")
    except ssmc.exceptions.ParameterNotFound as err:
        raise Exception(err)

account_id = boto3.client('sts').get_caller_identity().get('Account') or os.getenv(
    'CDK_DEFAULT_ACCOUNT'
)


# Configuration of the cdk.json SSM or in Repository
ssmc = boto3.client('ssm')
try:
    print("Trying to get cdkjson parameter from SSM")
    response = ssmc.get_parameter(Name="/dataall/v1m1m0/cdkjson")
    cdkjson = json.loads(response['Parameter']['Value']).get('context')
    print(f"context = {str(cdkjson)}")

    app = App(context=cdkjson)


except ssmc.exceptions.ParameterNotFound:
    print("SSM parameter not found - Proceeding with cdk.json and cdk.context.json in code")
    app = App()

git_branch = app.node.try_get_context('git_branch') or 'main'
print("git_branch")

cdk_pipeline_region = app.node.try_get_context('tooling_region') or os.getenv('CDK_DEFAULT_REGION')

target_envs = app.node.try_get_context('DeploymentEnvironments') or [
    {'envname': 'dev', 'account': account_id, 'region': 'eu-west-1'}
]

resource_prefix = app.node.try_get_context('resource_prefix') or 'dataall'

env = Environment(account=account_id, region=cdk_pipeline_region)

pipeline = PipelineStack(
    app,
    "{resource_prefix}-{git_branch}-cicd-stack".format(resource_prefix=resource_prefix,git_branch=git_branch),
    env=env,
    target_envs=target_envs,
    git_branch=git_branch,
    resource_prefix=resource_prefix,
)

Aspects.of(app).add(AwsSolutionsChecks(reports=True, verbose=False))

NagSuppressions.add_stack_suppressions(
    pipeline,
    suppressions=[
        NagPackSuppression(id=rule_suppressed['id'], reason=rule_suppressed['reason'])
        for rule_suppressed in PIPELINE_STACK_CDK_NAG_EXCLUSIONS
    ],
    apply_to_nested_stacks=True,
)

app.synth()
