import os
import json
import pytest
from aws_cdk import App
from aws_cdk.assertions import Template

from dataall.core.environment.db.environment_models import Environment
from dataall.modules.datapipelines.cdk.datapipelines_pipeline import PipelineStack
from dataall.modules.datapipelines.db.datapipelines_models import DataPipeline, DataPipelineEnvironment
from dataall.modules.datapipelines.db.datapipelines_repositories import DatapipelinesRepository
from tests.skip_conditions import checkov_scan


@pytest.fixture(scope='module', autouse=True)
def pipeline_db(db, env_fixture: Environment, group) -> DataPipeline:
    with db.scoped_session() as session:
        pipeline = DataPipeline(
            label='thistable',
            owner='me',
            AwsAccountId=env_fixture.AwsAccountId,
            region=env_fixture.region,
            environmentUri=env_fixture.environmentUri,
            repo='pipeline',
            SamlGroupName=group.name,
            devStrategy='trunk',
        )
        session.add(pipeline)
    yield pipeline


@pytest.fixture(scope='module', autouse=True)
def pip_envs(db, env_fixture: Environment, pipeline_db: DataPipeline) -> DataPipelineEnvironment:
    with db.scoped_session() as session:
        pipeline_env2 = DataPipelineEnvironment(
            owner='me',
            label=f'{pipeline_db.label}-{env_fixture.label}',
            environmentUri=env_fixture.environmentUri,
            environmentLabel=env_fixture.label,
            pipelineUri=pipeline_db.DataPipelineUri,
            pipelineLabel=pipeline_db.label,
            envPipelineUri=f'{pipeline_db.DataPipelineUri}{env_fixture.environmentUri}',
            AwsAccountId=env_fixture.AwsAccountId,
            region=env_fixture.region,
            stage='dev',
            order=1,
            samlGroupName='admins',
        )

        session.add(pipeline_env2)

    yield DatapipelinesRepository.query_pipeline_environments(session=session, uri=pipeline_db.DataPipelineUri)


@pytest.fixture(scope='function', autouse=True)
def patch_methods(mocker, db, pipeline_db, env_fixture, pip_envs, org_fixture):
    mocker.patch(
        'dataall.modules.datapipelines.cdk.datapipelines_pipeline.PipelineStack.get_engine',
        return_value=db,
    )
    mocker.patch(
        'dataall.base.aws.sts.SessionHelper.get_delegation_role_name',
        return_value='dataall-pivot-role-name-pytest',
    )
    mocker.patch(
        'dataall.modules.datapipelines.cdk.datapipelines_pipeline.PipelineStack.get_target',
        return_value=pipeline_db,
    )
    mocker.patch(
        'dataall.modules.datapipelines.cdk.datapipelines_pipeline.PipelineStack.get_pipeline_cicd_environment',
        return_value=env_fixture,
    )
    mocker.patch(
        'dataall.modules.datapipelines.cdk.datapipelines_pipeline.PipelineStack.get_pipeline_environments',
        return_value=pip_envs,
    )
    mocker.patch(
        'dataall.modules.datapipelines.cdk.datapipelines_pipeline.PipelineStack._set_env_vars',
        return_value=(os.environ, True),
    )
    mocker.patch(
        'dataall.modules.datapipelines.cdk.datapipelines_pipeline.PipelineStack._check_repository', return_value=False
    )
    mocker.patch('dataall.core.stacks.services.runtime_stacks_tagging.TagsUtil.get_engine', return_value=db)
    mocker.patch(
        'dataall.core.stacks.services.runtime_stacks_tagging.TagsUtil.get_target',
        return_value=pipeline_db,
    )
    mocker.patch(
        'dataall.core.stacks.services.runtime_stacks_tagging.TagsUtil.get_environment',
        return_value=env_fixture,
    )
    mocker.patch(
        'dataall.core.stacks.services.runtime_stacks_tagging.TagsUtil.get_organization',
        return_value=org_fixture,
    )


def test_resources_created(pipeline_db):
    app = App()
    stack = PipelineStack(app, 'Pipeline', target_uri=pipeline_db.DataPipelineUri)
    template = Template.from_stack(stack)
    # TODO: Add more assertions
    template.resource_count_is('AWS::CodeCommit::Repository', 1)
    template.resource_count_is('AWS::CodePipeline::Pipeline', 1)
    template.resource_count_is('AWS::CodeBuild::Project', 1)


@checkov_scan
def test_checkov(pipeline_db):
    app = App()
    stack = PipelineStack(app, 'Pipeline', target_uri=pipeline_db.DataPipelineUri)
    template = json.dumps(app.synth().get_stack_by_name('Pipeline').template)
    with open('checkov_pipeline_synth.json', 'w') as f:
        f.write(template)
