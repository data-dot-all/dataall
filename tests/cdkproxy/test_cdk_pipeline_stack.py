import json

import pytest
from aws_cdk import App

from dataall.cdkproxy.stacks.cdk_pipeline import CDKPipelineStack


@pytest.fixture(scope='function', autouse=True)
def patch_methods(mocker, db, pipeline1, env, pip_envs, org):
    mocker.patch(
        'dataall.cdkproxy.stacks.cdk_pipeline.CDKPipelineStack.get_engine',
        return_value=db,
    )
    mocker.patch(
        'dataall.aws.handlers.sts.SessionHelper.get_delegation_role_name',
        return_value="dataall-pivot-role-name-pytest",
    )
    mocker.patch(
        'dataall.cdkproxy.stacks.cdk_pipeline.CDKPipelineStack.get_target',
        return_value=pipeline1,
    )
    mocker.patch(
        'dataall.cdkproxy.stacks.cdk_pipeline.CDKPipelineStack.get_pipeline_cicd_environment',
        return_value=env,
    )
    mocker.patch(
        'dataall.cdkproxy.stacks.cdk_pipeline.CDKPipelineStack.get_pipeline_environments',
        return_value=pip_envs,
    )
    mocker.patch(
        'dataall.utils.runtime_stacks_tagging.TagsUtil.get_engine', return_value=db
    )
    mocker.patch(
        'dataall.utils.runtime_stacks_tagging.TagsUtil.get_target',
        return_value=pipeline1,
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
def template1(pipeline1):
    app = App()
    CDKPipelineStack(app, 'CDKPipeline', target_uri=pipeline1.DataPipelineUri)
    return json.dumps(app.synth().get_stack_by_name('CDKPipeline').template)


def test_resources_created_cdk_trunk(template1):
    assert 'AWS::CodeCommit::Repository' in template1

