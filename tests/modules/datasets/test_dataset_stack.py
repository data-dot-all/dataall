import json

import pytest
from aws_cdk import App

from dataall.db.models import Environment
from dataall.modules.datasets.cdk.dataset_stack import DatasetStack
from dataall.modules.datasets_base.db.models import Dataset

from tests.cdkproxy.conftest import *


@pytest.fixture(scope='module', autouse=True)
def dataset(db, env: Environment) -> Dataset:
    with db.scoped_session() as session:
        dataset = Dataset(
            label='thisdataset',
            environmentUri=env.environmentUri,
            organizationUri=env.organizationUri,
            name='thisdataset',
            description='test',
            AwsAccountId=env.AwsAccountId,
            region=env.region,
            S3BucketName='bucket',
            GlueDatabaseName='db',
            IAMDatasetAdminRoleArn='role',
            IAMDatasetAdminUserArn='xxx',
            KmsAlias='xxx',
            owner='me',
            confidentiality='C1',
            businessOwnerEmail='jeff',
            businessOwnerDelegationEmails=['andy'],
            SamlAdminGroupName='admins',
            GlueCrawlerName='dhCrawler',
        )
        session.add(dataset)
    yield dataset


@pytest.fixture(scope='function', autouse=True)
def patch_methods(mocker, db, dataset, env, org):
    mocker.patch('dataall.modules.datasets.cdk.dataset_stack.DatasetStack.get_engine', return_value=db)
    mocker.patch(
        'dataall.modules.datasets.cdk.dataset_stack.DatasetStack.get_target', return_value=dataset
    )
    mocker.patch(
        'dataall.aws.handlers.sts.SessionHelper.get_delegation_role_name',
        return_value="dataall-pivot-role-name-pytest",
    )
    mocker.patch(
        'dataall.aws.handlers.lakeformation.LakeFormation.check_existing_lf_registered_location',
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
    DatasetStack(app, 'Dataset', target_uri=dataset.datasetUri)
    return json.dumps(app.synth().get_stack_by_name('Dataset').template)


def test_resources_created(template):
    assert 'AWS::S3::Bucket' in template
    assert 'AWS::KMS::Key' in template
    assert 'AWS::IAM::Role' in template
    assert 'AWS::IAM::Policy' in template
    assert 'AWS::S3::BucketPolicy' in template
    assert 'AWS::Glue::Job' in template
