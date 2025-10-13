import random
from unittest.mock import MagicMock

import pytest

from dataall.base.context import set_context, RequestContext, dispose_context
from dataall.core.environment.db.environment_models import Environment, EnvironmentGroup
from dataall.core.organizations.db.organization_models import Organization
from dataall.core.permissions.services.resource_policy_service import ResourcePolicyService
from dataall.modules.shares_base.services.shares_enums import ShareableType, PrincipalType
from dataall.modules.shares_base.db.share_object_models import ShareObject, ShareObjectItem
from dataall.modules.shares_base.services.share_permissions import SHARE_OBJECT_REQUESTER, SHARE_OBJECT_APPROVER
from dataall.modules.datasets_base.services.datasets_enums import ConfidentialityClassification
from dataall.modules.s3_datasets.services.dataset_permissions import DATASET_TABLE_ALL
from dataall.modules.s3_datasets.db.dataset_models import S3Dataset, DatasetTable, DatasetStorageLocation
from dataall.modules.datasets_base.db.dataset_models import DatasetBase
from dataall.modules.s3_datasets.services.dataset_permissions import DATASET_ALL


@pytest.fixture(scope='module', autouse=True)
def patch_dataset_methods(module_mocker):
    module_mocker.patch(
        'dataall.modules.s3_datasets.services.dataset_service.DatasetService._check_dataset_account', return_value=True
    )
    module_mocker.patch(
        'dataall.modules.s3_datasets.services.dataset_service.DatasetService._deploy_dataset_stack', return_value=True
    )
    s3_mock_client = MagicMock()
    glue_mock_client = MagicMock()
    module_mocker.patch(
        'dataall.modules.s3_datasets.services.dataset_profiling_service.S3ProfilerClient', s3_mock_client
    )
    module_mocker.patch(
        'dataall.modules.s3_datasets.services.dataset_profiling_service.GlueDatasetProfilerClient', glue_mock_client
    )
    s3_mock_client().get_profiling_results_from_s3.return_value = '{"results": "yes"}'
    glue_mock_client().run_job.return_value = True

    module_mocker.patch(
        'dataall.modules.datasets_base.services.datasets_enums.ConfidentialityClassification.validate_confidentiality_level',
        return_value=True,
    )

    confidentiality_classification_mocker = MagicMock()
    module_mocker.patch(
        'dataall.modules.datasets_base.services.datasets_enums.ConfidentialityClassification',
        return_value=confidentiality_classification_mocker,
    )
    # Return the input when mocking. This mock avoids checking the custom_confidentiality_mapping value in the actual function and just returns  whatever confidentiality value is supplied for pytests
    confidentiality_classification_mocker().side_effect = lambda input: input


@pytest.fixture(scope='module', autouse=True)
def dataset(client, patch_es, patch_dataset_methods):
    cache = {}

    def factory(
        org: Organization,
        env: Environment,
        name: str,
        owner: str,
        group: str,
        confidentiality: str = None,
        autoApprovalEnabled: bool = False,
    ) -> S3Dataset:
        key = f'{org.organizationUri}-{env.environmentUri}-{name}-{group}'
        if cache.get(key):
            print('found in cache ', cache[key])
            return cache.get(key)
        response = client.query(
            """
            mutation CreateDataset($input:NewDatasetInput!){
                createDataset(
                input:$input
                ){
                    datasetUri
                    label
                    description
                    owner
                    SamlAdminGroupName
                    enableExpiration
                    expirySetting
                    expiryMinDuration
                    expiryMaxDuration
                    restricted {
                      AwsAccountId
                      region
                      KmsAlias
                      S3BucketName
                      GlueDatabaseName
                      IAMDatasetAdminRoleArn
                    }
                    tables{
                     nodes{
                      tableUri
                     }
                    }
                    locations{
                     nodes{
                      locationUri
                     }
                    }
                    stack{
                        stack
                        status
                        stackUri
                        targetUri
                        accountid
                        region
                        stackid
                        link
                        outputs
                        resources

                    }
                    topics
                    language
                    confidentiality
                    autoApprovalEnabled
                    terms{
                        count
                        nodes{
                            __typename
                            ...on Term {
                                nodeUri
                                path
                                label
                            }
                        }
                    }
                    environment {
                      environmentUri
                      label
                      region
                      organization {
                        organizationUri
                        label
                      }
                    }
                    statistics{
                        tables
                        locations
                        upvotes
                    }
                }
            }
            """,
            username=owner,
            groups=[group],
            input={
                'owner': owner,
                'label': f'{name}',
                'description': 'test dataset {name}',
                'businessOwnerEmail': 'jeff@amazon.com',
                'tags': random_tags(),
                'businessOwnerDelegationEmails': random_emails(),
                'environmentUri': env.environmentUri,
                'SamlAdminGroupName': group or random_group(),
                'organizationUri': org.organizationUri,
                'confidentiality': confidentiality or ConfidentialityClassification.Unclassified.value,
                'autoApprovalEnabled': autoApprovalEnabled,
            },
        )
        print('==>', response)
        return response.data.createDataset

    yield factory


@pytest.fixture(scope='module', autouse=True)
def table(db):
    cache = {}

    def factory(dataset: S3Dataset, name, username) -> DatasetTable:
        key = f'{dataset.datasetUri}-{name}'
        if cache.get(key):
            return cache.get(key)
        with db.scoped_session() as session:
            table = DatasetTable(
                name=name,
                label=name,
                owner=username,
                datasetUri=dataset.datasetUri,
                GlueDatabaseName=dataset.restricted.GlueDatabaseName,
                GlueTableName=name,
                region=dataset.restricted.region,
                AWSAccountId=dataset.restricted.AwsAccountId,
                S3BucketName=dataset.restricted.S3BucketName,
                S3Prefix=f'{name}',
            )
            session.add(table)
            session.commit()

            ResourcePolicyService.attach_resource_policy(
                session=session,
                group=dataset.SamlAdminGroupName,
                permissions=DATASET_TABLE_ALL,
                resource_uri=table.tableUri,
                resource_type=DatasetTable.__name__,
            )
        return table

    yield factory


@pytest.fixture(scope='module')
def dataset_fixture(env_fixture, org_fixture, dataset, group) -> S3Dataset:
    yield dataset(
        org=org_fixture,
        env=env_fixture,
        name='dataset1',
        owner=env_fixture.owner,
        group=group.name,
    )


@pytest.fixture(scope='module')
def dataset_confidential_fixture(env_fixture, org_fixture, dataset, group) -> S3Dataset:
    yield dataset(
        org=org_fixture,
        env=env_fixture,
        name='dataset2',
        owner=env_fixture.owner,
        group=group.name,
        confidentiality=ConfidentialityClassification.Secret.value,
    )


@pytest.fixture(scope='module')
def table_fixture(db, dataset_fixture, table, group, user):
    table1 = table(dataset=dataset_fixture, name='table1', username=user.username)

    with db.scoped_session() as session:
        ResourcePolicyService.attach_resource_policy(
            session=session,
            group=group.groupUri,
            permissions=DATASET_TABLE_ALL,
            resource_uri=table1.tableUri,
            resource_type=DatasetTable.__name__,
        )
    yield table1


@pytest.fixture(scope='module')
def table_confidential_fixture(db, dataset_confidential_fixture, table, group, user):
    table2 = table(dataset=dataset_confidential_fixture, name='table2', username=user.username)

    with db.scoped_session() as session:
        ResourcePolicyService.attach_resource_policy(
            session=session,
            group=group.groupUri,
            permissions=DATASET_TABLE_ALL,
            resource_uri=table2.tableUri,
            resource_type=DatasetTable.__name__,
        )
    yield table2


@pytest.fixture(scope='module')
def folder_fixture(db, dataset_fixture):
    with db.scoped_session() as session:
        location = DatasetStorageLocation(
            datasetUri=dataset_fixture.datasetUri,
            AWSAccountId='12345678901',
            S3Prefix='S3prefix',
            label='label',
            owner='foo',
            name='name',
            S3BucketName='S3BucketName',
            region='eu-west-1',
        )
        session.add(location)
    yield location


@pytest.fixture(scope='module')
def dataset_model(db):
    def factory(
        organization: Organization, environment: Environment, label: str, autoApprovalEnabled: bool = False
    ) -> S3Dataset:
        with db.scoped_session() as session:
            dataset = S3Dataset(
                organizationUri=organization.organizationUri,
                environmentUri=environment.environmentUri,
                label=label,
                owner=environment.owner,
                stewards=environment.SamlGroupName,
                SamlAdminGroupName=environment.SamlGroupName,
                businessOwnerDelegationEmails=['foo@amazon.com'],
                name=label,
                S3BucketName=label,
                GlueDatabaseName='gluedatabase',
                KmsAlias='kmsalias',
                AwsAccountId=environment.AwsAccountId,
                region=environment.region,
                IAMDatasetAdminUserArn=f'arn:aws:iam::{environment.AwsAccountId}:user/dataset',
                IAMDatasetAdminRoleArn=f'arn:aws:iam::{environment.AwsAccountId}:role/dataset',
                autoApprovalEnabled=autoApprovalEnabled,
            )
            session.add(dataset)
            session.commit()

            ResourcePolicyService.attach_resource_policy(
                session=session,
                group=environment.SamlGroupName,
                permissions=DATASET_ALL,
                resource_uri=dataset.datasetUri,
                resource_type=DatasetBase.__name__,
            )
            return dataset

    yield factory


@pytest.fixture(scope='module', autouse=True)
def location(db):
    cache = {}

    def factory(dataset: S3Dataset, name, username) -> DatasetStorageLocation:
        key = f'{dataset.datasetUri}-{name}'
        if cache.get(key):
            return cache.get(key)
        with db.scoped_session() as session:
            ds_location = DatasetStorageLocation(
                name=name,
                label=name,
                owner=username,
                datasetUri=dataset.datasetUri,
                S3BucketName=dataset.restricted.S3BucketName,
                region=dataset.restricted.region,
                AWSAccountId=dataset.restricted.AwsAccountId,
                S3Prefix=f'{name}',
            )
            session.add(ds_location)
        return ds_location

    yield factory


@pytest.fixture(scope='module')
def share_item(db):
    def factory(
        share: ShareObject,
        table: DatasetTable,
        status: str,
        healthStatus: str = None,
    ) -> ShareObjectItem:
        with db.scoped_session() as session:
            share_item = ShareObjectItem(
                shareUri=share.shareUri,
                owner='alice',
                itemUri=table.tableUri,
                itemType=ShareableType.Table.value,
                itemName=table.name,
                status=status,
                healthStatus=healthStatus,
            )
            session.add(share_item)
            session.commit()
            return share_item

    yield factory


@pytest.fixture(scope='module')
def share(db):
    def factory(
        dataset: S3Dataset, environment: Environment, env_group: EnvironmentGroup, owner: str, status: str
    ) -> ShareObject:
        with db.scoped_session() as session:
            share = ShareObject(
                datasetUri=dataset.datasetUri,
                environmentUri=environment.environmentUri,
                owner=owner,
                groupUri=env_group.groupUri,
                principalId=env_group.groupUri,
                principalType=PrincipalType.Group.value,
                principalRoleName=env_group.environmentIAMRoleName,
                status=status,
            )
            session.add(share)
            session.commit()

            ResourcePolicyService.attach_resource_policy(
                session=session,
                group=env_group.groupUri,
                permissions=SHARE_OBJECT_REQUESTER,
                resource_uri=share.shareUri,
                resource_type=ShareObject.__name__,
            )
            ResourcePolicyService.attach_resource_policy(
                session=session,
                group=dataset.SamlAdminGroupName,
                permissions=SHARE_OBJECT_APPROVER,
                resource_uri=share.shareUri,
                resource_type=ShareObject.__name__,
            )
            ResourcePolicyService.attach_resource_policy(
                session=session,
                group=dataset.stewards,
                permissions=SHARE_OBJECT_APPROVER,
                resource_uri=share.shareUri,
                resource_type=ShareObject.__name__,
            )
            session.commit()
            return share

    yield factory


def random_email():
    names = ['andy', 'bill', 'satya', 'sundar']
    corps = ['google.com', 'amazon.com', 'microsoft.com']
    return f'{random.choice(names)}@{random.choice(corps)}'


def random_emails():
    emails = []
    for i in range(1, 2 + random.choice([2, 3, 4])):
        emails.append(random_email())
    return emails


def random_group():
    prefixes = ['big', 'small', 'pretty', 'shiny']
    names = ['team', 'people', 'group']
    lands = ['snow', 'ice', 'green', 'high']
    return f'{random.choice(prefixes).capitalize()}{random.choice(names).capitalize()}From{random.choice(lands).capitalize()}land'


def random_tag():
    return random.choice(['sales', 'finances', 'sites', 'people', 'products', 'partners', 'operations'])


def random_tags():
    return [random_tag() for i in range(1, random.choice([2, 3, 4, 5]))]


@pytest.fixture(scope='function')
def api_context_1(db, user, group):
    yield set_context(RequestContext(db_engine=db, username=user.username, groups=[group.name], user_id=user.username))
    dispose_context()
