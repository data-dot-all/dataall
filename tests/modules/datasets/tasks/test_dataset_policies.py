from unittest.mock import MagicMock

from dataall.api.constants import OrganisationUserRole
from dataall.core.environment.db.models import Environment
from dataall.modules.datasets_base.db.models import DatasetTable, Dataset
from dataall.modules.datasets.tasks.bucket_policy_updater import BucketPoliciesUpdater
import pytest
import dataall


@pytest.fixture(scope='module', autouse=True)
def org(db):
    with db.scoped_session() as session:
        org = dataall.db.models.Organization(
            label='org',
            owner='alice',
            tags=[],
            description='desc',
            SamlGroupName='admins',
            userRoleInOrganization=OrganisationUserRole.Owner.value,
        )
        session.add(org)
    yield org


@pytest.fixture(scope='module', autouse=True)
def env(org, db):
    with db.scoped_session() as session:
        env = Environment(
            organizationUri=org.organizationUri,
            AwsAccountId='12345678901',
            region='eu-west-1',
            label='org',
            owner='alice',
            tags=[],
            description='desc',
            SamlGroupName='admins',
            EnvironmentDefaultIAMRoleName='EnvRole',
            EnvironmentDefaultIAMRoleArn='arn:aws::123456789012:role/EnvRole/GlueJobSessionRunner',
            CDKRoleArn='arn:aws::123456789012:role/EnvRole',
            userRoleInEnvironment='999',
        )
        session.add(env)
    yield env


@pytest.fixture(scope='module', autouse=True)
def sync_dataset(org, env, db):
    with db.scoped_session() as session:
        dataset = Dataset(
            organizationUri=org.organizationUri,
            environmentUri=env.environmentUri,
            label='label',
            owner='foo',
            SamlAdminGroupName='foo',
            businessOwnerDelegationEmails=['foo@amazon.com'],
            businessOwnerEmail=['bar@amazon.com'],
            name='name',
            S3BucketName='S3BucketName',
            GlueDatabaseName='GlueDatabaseName',
            KmsAlias='kmsalias',
            AwsAccountId='123456789012',
            region='eu-west-1',
            IAMDatasetAdminUserArn=f'arn:aws:iam::123456789012:user/dataset',
            IAMDatasetAdminRoleArn=f'arn:aws:iam::123456789012:role/dataset',
            imported=True,
        )
        session.add(dataset)
    yield dataset


@pytest.fixture(scope='module', autouse=True)
def table(org, env, db, sync_dataset):
    with db.scoped_session() as session:
        table = DatasetTable(
            datasetUri=sync_dataset.datasetUri,
            AWSAccountId='12345678901',
            S3Prefix='S3prefix',
            label='label',
            owner='foo',
            name='name',
            GlueTableName='table1',
            S3BucketName='S3BucketName',
            GlueDatabaseName='GlueDatabaseName',
            region='eu-west-1',
        )
        session.add(table)
    yield table


def test_prefix_delta():
    s = 's3://insite-data-lake-core-alpha-eu-west-1/forecast/ship_plan/insite_version=0.1/insite_region_id=2/ship_plan.delta/_symlink_format_manifest/*'
    delta_path = s.split('/_symlink_format_manifest')[0].split('/')[-1]
    prefix = s.split(f'/{delta_path}')[0]
    assert (
        prefix
        == 's3://insite-data-lake-core-alpha-eu-west-1/forecast/ship_plan/insite_version=0.1/insite_region_id=2'
    )
    prefix = 'arn:aws:s3:::insite-data-lake-core-alpha-eu-west-1/forecast/ship_plan/insite_version=0.1/insite_region_id=2'
    bucket = prefix.split('arn:aws:s3:::')[1].split('/')[0]
    assert bucket == 'insite-data-lake-core-alpha-eu-west-1'


def test_group_prefixes_by_accountid(db, mocker):
    statements = {}
    updater = BucketPoliciesUpdater(db)
    updater.group_prefixes_by_accountid('675534', 'prefix1', statements)
    updater.group_prefixes_by_accountid('675534', 'prefix2', statements)
    updater.group_prefixes_by_accountid('675534', 'prefix3', statements)
    updater.group_prefixes_by_accountid('675534', 'prefix3', statements)
    updater.group_prefixes_by_accountid('3455', 'prefix4', statements)
    assert len(set(statements['675534'])) == 3
    policy = {
        'Version': '2012-10-17',
        'Statement': [
            {
                'Sid': f'OwnerAccount',
                'Effect': 'Allow',
                'Action': ['s3:*'],
                'Resource': [
                    f'arn:aws:s3:::',
                    f'arn:aws:s3:::',
                ],
                'Principal': {'AWS': f'arn:aws:iam::root'},
            },
            {
                'Sid': f'DH675534',
                'Effect': 'Allow',
                'Action': ['s3:*'],
                'Resource': [
                    f'prefix3',
                    f'prefix2',
                ],
                'Principal': {'AWS': '675534'},
            },
        ]
    }
    BucketPoliciesUpdater.update_policy(statements, policy)
    assert policy


def test_handler(org, env, db, sync_dataset, mocker):
    s3_client = MagicMock()
    mocker.patch('dataall.modules.datasets.tasks.bucket_policy_updater.S3BucketPolicyClient', s3_client)
    s3_client().get_bucket_policy.return_value = {'Version': '2012-10-17', 'Statement': []}
    s3_client().put_bucket_policy.return_value = {'status': 'SUCCEEDED'}

    updater = BucketPoliciesUpdater(db)
    assert len(updater.sync_imported_datasets_bucket_policies()) == 1
    assert updater.sync_imported_datasets_bucket_policies()[0]['status'] == 'SUCCEEDED'
