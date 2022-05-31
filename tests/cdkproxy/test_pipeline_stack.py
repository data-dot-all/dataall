import json

import pytest
from aws_cdk import App

from dataall.cdkproxy.stacks.pipeline import PipelineStack


@pytest.fixture(scope='function', autouse=True)
def patch_methods(mocker, db, pipeline, env, org):
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
        return_value=pipeline,
    )
    mocker.patch(
        'dataall.cdkproxy.stacks.pipeline.PipelineStack.get_pipeline_environment',
        return_value=env,
    )
    mocker.patch(
        'dataall.utils.runtime_stacks_tagging.TagsUtil.get_engine', return_value=db
    )
    mocker.patch(
        'dataall.utils.runtime_stacks_tagging.TagsUtil.get_target',
        return_value=pipeline,
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
def template(pipeline):
    app = App()
    PipelineStack(app, 'Pipeline', target_uri=pipeline.sqlPipelineUri)
    return json.dumps(app.synth().get_stack_by_name('Pipeline').template)


def test_resources_created(template):
    assert 'AWS::CodePipeline::Pipeline' in template
    assert 'AWS::CodeBuild::Project' in template
    assert 'AWS::IAM::Role' in template
    assert 'AWS::S3::Bucket' in template
    assert 'AWS::Lambda::Function' in template
