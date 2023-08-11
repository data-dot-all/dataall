import json
import os

import pytest
from aws_cdk import App, Stack
from aws_cdk.assertions import Template

from dataall.core.environment.db.models import Environment
from dataall.modules.datapipelines.cdk.datapipelines_pipeline import PipelineStack
from dataall.modules.datapipelines.db.models import DataPipeline, DataPipelineEnvironment
from dataall.modules.datapipelines.db.datapipelines_repository import DatapipelinesRepository


@pytest.fixture(scope='module', autouse=True)
def pipeline2(db, env: Environment) -> DataPipeline:
    with db.scoped_session() as session:
        pipeline = DataPipeline(
            label='thistable',
            owner='me',
            AwsAccountId=env.AwsAccountId,
            region=env.region,
            environmentUri=env.environmentUri,
            repo='pipeline',
            SamlGroupName='admins',
            devStrategy='trunk'
        )
        session.add(pipeline)
    yield pipeline


@pytest.fixture(scope='module', autouse=True)
def pip_envs(db, env: Environment, pipeline2: DataPipeline) -> DataPipelineEnvironment:
    with db.scoped_session() as session:
        pipeline_env2 = DataPipelineEnvironment(
            owner='me',
            label=f"{pipeline2.label}-{env.label}",
            environmentUri=env.environmentUri,
            environmentLabel=env.label,
            pipelineUri=pipeline2.DataPipelineUri,
            pipelineLabel=pipeline2.label,
            envPipelineUri=f"{pipeline2.DataPipelineUri}{env.environmentUri}",
            AwsAccountId=env.AwsAccountId,
            region=env.region,
            stage='dev',
            order=1,
            samlGroupName='admins'
        )

        session.add(pipeline_env2)

    yield DatapipelinesRepository.query_pipeline_environments(session=session, uri=pipeline2.DataPipelineUri)


@pytest.fixture(scope='function', autouse=True)
def patch_methods(mocker, db, pipeline2, env, pip_envs, org):
    mocker.patch(
        'dataall.modules.datapipelines.cdk.datapipelines_pipeline.PipelineStack.get_engine',
        return_value=db,
    )
    mocker.patch(
        'dataall.base.aws.sts.SessionHelper.get_delegation_role_name',
        return_value="dataall-pivot-role-name-pytest",
    )
    mocker.patch(
        'dataall.modules.datapipelines.cdk.datapipelines_pipeline.PipelineStack.get_target',
        return_value=pipeline2,
    )
    mocker.patch(
        'dataall.modules.datapipelines.cdk.datapipelines_pipeline.PipelineStack.get_pipeline_cicd_environment',
        return_value=env,
    )
    mocker.patch(
        'dataall.modules.datapipelines.cdk.datapipelines_pipeline.PipelineStack.get_pipeline_environments',
        return_value=pip_envs,
    )
    mocker.patch(
        'dataall.modules.datapipelines.cdk.datapipelines_pipeline.PipelineStack._set_env_vars',
        return_value=(os.environ, True)
    )
    mocker.patch(
        'dataall.modules.datapipelines.cdk.datapipelines_pipeline.PipelineStack._check_repository',
        return_value=False
    )
    mocker.patch(
        'dataall.core.stacks.services.runtime_stacks_tagging.TagsUtil.get_engine', return_value=db
    )
    mocker.patch(
        'dataall.core.stacks.services.runtime_stacks_tagging.TagsUtil.get_target',
        return_value=pipeline2,
    )
    mocker.patch(
        'dataall.core.stacks.services.runtime_stacks_tagging.TagsUtil.get_environment',
        return_value=env,
    )
    mocker.patch(
        'dataall.core.stacks.services.runtime_stacks_tagging.TagsUtil.get_organization',
        return_value=org,
    )


def test_resources_created(pipeline2):
    app = App()
    stack = PipelineStack(app, 'Pipeline', target_uri=pipeline2.DataPipelineUri)
    template = Template.from_stack(stack)
    # TODO: Add more assertions
    template.resource_count_is("AWS::CodeCommit::Repository", 1)
    template.resource_count_is("AWS::CodePipeline::Pipeline", 1)
    template.resource_count_is("AWS::CodeBuild::Project", 1)
