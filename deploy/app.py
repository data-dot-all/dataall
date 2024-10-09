#!/usr/bin/env python3

import json
import logging
import os
import subprocess
import re

import boto3
import botocore
from aws_cdk import App, Environment, Aspects
from cdk_nag import AwsSolutionsChecks, NagSuppressions, NagPackSuppression

from stacks.cdk_nag_exclusions import PIPELINE_STACK_CDK_NAG_EXCLUSIONS
from stacks.pipeline import PipelineStack

LOGGING_FORMAT = '[%(asctime)s][%(filename)-13s:%(lineno)3d] %(message)s'
logging.basicConfig(level=logging.INFO, format=LOGGING_FORMAT)
logger = logging.getLogger(__name__)


if not os.environ.get('DATAALL_REPO_BRANCH', None):
    # Configuration of the branch in first deployment
    git_branch = (
        subprocess.Popen(['git', 'branch', '--show-current'], stdout=subprocess.PIPE)
        .stdout.read()
        .decode('utf-8')
        .rstrip('\n')
    )
else:
    # Configuration of the branch in subsequent deployments
    git_branch = os.environ.get('DATAALL_REPO_BRANCH')


git_branch = re.sub('[^a-zA-Z0-9-_]', '', git_branch)[:99] if git_branch != '' else 'main'

# Configuration of the cdk.json SSM or in Repository
if os.getenv('GITHUB_ACTIONS'):
    logger.info('Running GitHub Actions')
    account_id = os.getenv('CDK_DEFAULT_ACCOUNT')
    region = os.getenv('CDK_DEFAULT_REGION', 'eu-west-1')
    app = App(
        context={
            f'availability-zones:account=111111111111:region={region}': [f'{region}a', f'{region}b', f'{region}c'],
            'availability-zones:account=111111111111:region=us-east-1': ['us-east-1a', 'us-east-1b', 'us-east-1c'],
        }
    )
else:
    account_id = boto3.client('sts').get_caller_identity().get('Account') or os.getenv('CDK_DEFAULT_ACCOUNT')
    try:
        logger.info('Trying to get cdkjson parameter from SSM')
        ssmc = boto3.client('ssm', os.getenv('CDK_DEFAULT_REGION', 'eu-west-1'))
        response = ssmc.get_parameter(Name=f'/dataall/{git_branch}/cdkjson')
        cdkjson = json.loads(response['Parameter']['Value']).get('context')

        app = App(context=cdkjson)
        logger.info('Loaded context from SSM')

    except (ssmc.exceptions.ParameterNotFound, botocore.exceptions.ClientError) as err:
        if isinstance(err, ssmc.exceptions.ParameterNotFound):
            logger.warning('SSM parameter not found - Proceeding with cdk.json and cdk.context.json in code')
        else:
            logger.error(err)

        app = App()
        logger.info('Loaded context from cdk.json file in repository')

cdk_pipeline_region = app.node.try_get_context('tooling_region') or os.getenv('CDK_DEFAULT_REGION', 'eu-west-1')

target_envs = app.node.try_get_context('DeploymentEnvironments') or [
    {'envname': 'dev', 'account': account_id, 'region': os.getenv('CDK_DEFAULT_REGION', 'eu-west-1')}
]

resource_prefix = app.node.try_get_context('resource_prefix') or 'dataall'

source = app.node.try_get_context('repository_source') or 'codecommit'
repo_string = app.node.try_get_context('repo_string') or 'awslabs/aws-dataall'
repo_connection_arn = app.node.try_get_context('repo_connection_arn')

env = Environment(account=account_id, region=cdk_pipeline_region)

pipeline = PipelineStack(
    app,
    '{resource_prefix}-{git_branch}-cicd-stack'.format(resource_prefix=resource_prefix, git_branch=git_branch),
    env=env,
    target_envs=target_envs,
    git_branch=git_branch,
    resource_prefix=resource_prefix,
    source=source,
    repo_string=repo_string,
    repo_connection_arn=repo_connection_arn,
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
