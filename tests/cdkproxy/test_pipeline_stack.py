import json

import pytest
from aws_cdk import App

from dataall.cdkproxy.stacks.pipeline import PipelineStack


@pytest.fixture(scope='function', autouse=True)
def patch_methods(mocker, db, pipeline2, env, pip_envs, org):
    mocker.patch(
        'dataall.cdkproxy.stacks.pipeline.PipelineStack.get_engine',
        return_value=db,
    )
    mocker.patch(
        'dataall.aws.handlers.sts.SessionHelper.get_delegation_role_name',
        return_value="dataall-pivot-role-name-pytest",
    )
    mocker.patch(
        'dataall.cdkproxy.stacks.pipeline.PipelineStack.get_target',
        return_value=pipeline2,
    )
    mocker.patch(
        'dataall.cdkproxy.stacks.pipeline.PipelineStack.get_pipeline_cicd_environment',
        return_value=env,
    )
    mocker.patch(
        'dataall.cdkproxy.stacks.pipeline.PipelineStack.get_pipeline_environments',
        return_value=pip_envs,
    )
    mocker.patch(
        'dataall.utils.runtime_stacks_tagging.TagsUtil.get_engine', return_value=db
    )
    mocker.patch(
        'dataall.utils.runtime_stacks_tagging.TagsUtil.get_target',
        return_value=pipeline2,
    )
    mocker.patch(
        'dataall.utils.runtime_stacks_tagging.TagsUtil.get_environment',
        return_value=env,
    )
    mocker.patch(
        'dataall.utils.runtime_stacks_tagging.TagsUtil.get_organization',
        return_value=org,
    )

@pytest.fixture(scope='function', autouse=True)
def template2(pipeline2):
    app = App()
    PipelineStack(app, 'Pipeline', target_uri=pipeline2.DataPipelineUri)
    return json.dumps(app.synth().get_stack_by_name('Pipeline').template)


def test_resources_created_cp_trunk(template2):
    assert 'AWS::CodeCommit::Repository' in template2
    assert 'AWS::CodePipeline::Pipeline' in template2
    assert 'AWS::CodeBuild::Project' in template2