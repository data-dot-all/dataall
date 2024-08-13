import json
from unittest.mock import MagicMock
import os
import pytest
from aws_cdk import App

from dataall.core.environment.db.environment_models import Environment
from dataall.modules.s3_datasets.cdk.dataset_stack import DatasetStack
from dataall.modules.s3_datasets.db.dataset_models import S3Dataset
from tests.skip_conditions import checkov_scan


@pytest.fixture(scope='module', autouse=True)
def dataset(db, env_fixture: Environment) -> S3Dataset:
    with db.scoped_session() as session:
        dataset = S3Dataset(
            label='thisdataset',
            environmentUri=env_fixture.environmentUri,
            organizationUri=env_fixture.organizationUri,
            name='thisdataset',
            description='test',
            AwsAccountId=env_fixture.AwsAccountId,
            region=env_fixture.region,
            S3BucketName='bucket',
            GlueDatabaseName='db',
            IAMDatasetAdminRoleArn='role',
            IAMDatasetAdminUserArn='xxx',
            KmsAlias='xxx',
            owner='me',
            confidentiality='C1',
            businessOwnerEmail='jeff',
            businessOwnerDelegationEmails=['andy'],
            SamlAdminGroupName=env_fixture.SamlGroupName,
            GlueCrawlerName='dhCrawler',
        )
        session.add(dataset)
    yield dataset


@pytest.fixture(scope='function', autouse=True)
def patch_methods(mocker, db, dataset, env_fixture, org_fixture):
    mocker.patch('dataall.modules.s3_datasets.cdk.dataset_stack.DatasetStack.get_engine', return_value=db)
    mocker.patch('dataall.modules.s3_datasets.cdk.dataset_stack.DatasetStack.get_target', return_value=dataset)
    mocker.patch(
        'dataall.base.aws.sts.SessionHelper.get_delegation_role_name',
        return_value='dataall-pivot-role-name-pytest',
    )
    lf_client = MagicMock()
    mocker.patch(
        'dataall.modules.s3_datasets.cdk.dataset_stack.LakeFormationDatasetClient',
        return_value=lf_client,
    )
    lf_client.return_value.check_existing_lf_registered_location = False
    mocker.patch(
        'dataall.core.stacks.services.runtime_stacks_tagging.TagsUtil.get_target',
        return_value=dataset,
    )
    mocker.patch(
        'dataall.core.stacks.services.runtime_stacks_tagging.TagsUtil.get_engine',
        return_value=db,
    )
    mocker.patch(
        'dataall.core.stacks.services.runtime_stacks_tagging.TagsUtil.get_environment',
        return_value=env_fixture,
    )
    mocker.patch(
        'dataall.core.stacks.services.runtime_stacks_tagging.TagsUtil.get_organization',
        return_value=org_fixture,
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


@checkov_scan
def test_checkov(template):
    with open('checkov_s3_dataset_synth.json', 'w') as f:
        f.write(template)
