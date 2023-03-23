import json

import pytest
from aws_cdk import App

from dataall.cdkproxy.stacks import Dataset


@pytest.fixture(scope='function', autouse=True)
def patch_methods(mocker, db, dataset, env, org):
    mocker.patch('dataall.cdkproxy.stacks.dataset.Dataset.get_engine', return_value=db)
    mocker.patch(
        'dataall.cdkproxy.stacks.dataset.Dataset.get_target', return_value=dataset
    )
    mocker.patch(
        'dataall.aws.handlers.sts.SessionHelper.get_delegation_role_name',
        return_value="dataall-pivot-role-name-pytest",
    )
    mocker.patch(
        'dataall.aws.handlers.lakeformation.LakeFormation.describe_resource',
        return_value=False,
    )
    mocker.patch(
        'dataall.utils.runtime_stacks_tagging.TagsUtil.get_target',
        return_value=dataset,
    )
    mocker.patch(
        'dataall.utils.runtime_stacks_tagging.TagsUtil.get_engine',
        return_value=db,
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
def template(dataset):
    app = App()
    Dataset(app, 'Dataset', target_uri=dataset.datasetUri)
    return json.dumps(app.synth().get_stack_by_name('Dataset').template)


def test_resources_created(template):
    assert 'AWS::S3::Bucket' in template
    assert 'AWS::KMS::Key' in template
    assert 'AWS::IAM::Role' in template
    assert 'AWS::Lambda::Function' in template
    assert 'AWS::IAM::Policy' in template
    assert 'AWS::S3::BucketPolicy' in template
    assert 'AWS::Glue::Job' in template
