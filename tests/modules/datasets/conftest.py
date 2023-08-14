import random
from unittest.mock import MagicMock

import pytest

from dataall.core.environment.db.models import Environment, EnvironmentGroup
from dataall.core.organizations.db.organization_models import Organization
from dataall.core.permissions.db.resource_policy import ResourcePolicy
from dataall.core.stacks.db.stack_models import Stack
from dataall.modules.dataset_sharing.db.enums import ShareableType, PrincipalType
from dataall.modules.dataset_sharing.db.models import ShareObject, ShareObjectItem
from dataall.modules.dataset_sharing.services.share_permissions import SHARE_OBJECT_REQUESTER, SHARE_OBJECT_APPROVER
from dataall.modules.datasets.api.dataset.enums import ConfidentialityClassification
from dataall.modules.datasets_base.services.permissions import DATASET_TABLE_READ
from dataall.modules.datasets import Dataset, DatasetTable, DatasetStorageLocation


@pytest.fixture(scope='module', autouse=True)
def patch_dataset_methods(module_mocker):
    module_mocker.patch(
        'dataall.modules.datasets.services.dataset_service.DatasetService.check_dataset_account', return_value=True
    )
    module_mocker.patch(
        'dataall.modules.datasets.services.dataset_service.DatasetService._deploy_dataset_stack',
        return_value=True
    )
    s3_mock_client = MagicMock()
    glue_mock_client = MagicMock()
    module_mocker.patch(
        'dataall.modules.datasets.services.dataset_profiling_service.S3ProfilerClient', s3_mock_client
    )
    module_mocker.patch(
        'dataall.modules.datasets.services.dataset_profiling_service.GlueDatasetProfilerClient', glue_mock_client
    )
    s3_mock_client().get_profiling_results_from_s3.return_value = '{"results": "yes"}'
    glue_mock_client().run_job.return_value = True


@pytest.fixture(scope='module', autouse=True)
def dataset(client, patch_es, patch_dataset_methods):
    cache = {}

    def factory(
        org: Organization,
        env: Environment,
        name: str,
        owner: str,
        group: str,
        confidentiality: str = None
    ) -> Dataset:
        key = f'{org.organizationUri}-{env.environmentUri}-{name}-{group}'
        if cache.get(key):
            print('found in cache ', cache[key])
            return cache.get(key)
        response = client.query(
            """
            mutation CreateDataset($input:NewDatasetInput){
                createDataset(
                input:$input
                ){
                    datasetUri
                    label
                    description
                    AwsAccountId
                    S3BucketName
                    GlueDatabaseName
                    owner
                    region,
                    businessOwnerEmail
                    businessOwnerDelegationEmails
                    SamlAdminGroupName
                    GlueCrawlerName
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
                    organization{
                        organizationUri
                        label
                    }
                    shares{
                        nodes{
                         shareUri
                        }
                    }
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
                    environment{
                        environmentUri
                        label
                        region
                        subscriptionsEnabled
                        subscriptionsProducersTopicImported
                        subscriptionsConsumersTopicImported
                        subscriptionsConsumersTopicName
                        subscriptionsProducersTopicName
                        organization{
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
                'confidentiality': confidentiality or ConfidentialityClassification.Unclassified.value

            },
        )
        print('==>', response)
        return response.data.createDataset

    yield factory


@pytest.fixture(scope='module', autouse=True)
def table(db):
    cache = {}

    def factory(dataset: Dataset, name, username) -> DatasetTable:
        key = f'{dataset.datasetUri}-{name}'
        if cache.get(key):
            return cache.get(key)
        with db.scoped_session() as session:
            table = DatasetTable(
                name=name,
                label=name,
                owner=username,
                datasetUri=dataset.datasetUri,
                GlueDatabaseName=dataset.GlueDatabaseName,
                GlueTableName=name,
                region=dataset.region,
                AWSAccountId=dataset.AwsAccountId,
                S3BucketName=dataset.S3BucketName,
                S3Prefix=f'{name}',
            )
            session.add(table)
            session.commit()

            ResourcePolicy.attach_resource_policy(
                session=session,
                group=dataset.SamlAdminGroupName,
                permissions=DATASET_TABLE_READ,
                resource_uri=table.tableUri,
                resource_type=DatasetTable.__name__
            )
        return table

    yield factory


@pytest.fixture(scope='module')
def dataset_fixture(env_fixture, org_fixture, dataset, group) -> Dataset:
    yield dataset(
        org=org_fixture,
        env=env_fixture,
        name='dataset1',
        owner=env_fixture.owner,
        group=group.name,
    )


@pytest.fixture(scope='module')
def table_fixture(db, dataset_fixture, table, group, user):
    table1 = table(dataset=dataset_fixture, name="table1", username=user.username)

    with db.scoped_session() as session:
        ResourcePolicy.attach_resource_policy(
            session=session,
            group=group.groupUri,
            permissions=DATASET_TABLE_READ,
            resource_uri=table1.tableUri,
            resource_type=DatasetTable.__name__,
        )
    yield table1


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


@pytest.fixture(scope="module")
def dataset_model(db):
    def factory(
        organization: Organization,
        environment: Environment,
        label: str,
    ) -> Dataset:
        with db.scoped_session() as session:
            dataset = Dataset(
                organizationUri=organization.organizationUri,
                environmentUri=environment.environmentUri,
                label=label,
                owner=environment.owner,
                stewards=environment.SamlGroupName,
                SamlAdminGroupName=environment.SamlGroupName,
                businessOwnerDelegationEmails=["foo@amazon.com"],
                name=label,
                S3BucketName=label,
                GlueDatabaseName="gluedatabase",
                KmsAlias="kmsalias",
                AwsAccountId=environment.AwsAccountId,
                region=environment.region,
                IAMDatasetAdminUserArn=f"arn:aws:iam::{environment.AwsAccountId}:user/dataset",
                IAMDatasetAdminRoleArn=f"arn:aws:iam::{environment.AwsAccountId}:role/dataset",
            )
            session.add(dataset)
            session.commit()
            return dataset

    yield factory


@pytest.fixture(scope='module', autouse=True)
def location(db):
    cache = {}

    def factory(dataset: Dataset, name, username) -> DatasetStorageLocation:
        key = f'{dataset.datasetUri}-{name}'
        if cache.get(key):
            return cache.get(key)
        with db.scoped_session() as session:
            ds_location = DatasetStorageLocation(
                name=name,
                label=name,
                owner=username,
                datasetUri=dataset.datasetUri,
                S3BucketName=dataset.S3BucketName,
                region=dataset.region,
                AWSAccountId=dataset.AwsAccountId,
                S3Prefix=f'{name}',
            )
            session.add(ds_location)
        return ds_location

    yield factory


@pytest.fixture(scope="module")
def share_item(db):
    def factory(
            share: ShareObject,
            table: DatasetTable,
            status: str
    ) -> ShareObjectItem:
        with db.scoped_session() as session:
            share_item = ShareObjectItem(
                shareUri=share.shareUri,
                owner="alice",
                itemUri=table.tableUri,
                itemType=ShareableType.Table.value,
                itemName=table.name,
                status=status,
            )
            session.add(share_item)
            session.commit()
            return share_item

    yield factory


@pytest.fixture(scope="module")
def share(db):
    def factory(
            dataset: Dataset,
            environment: Environment,
            env_group: EnvironmentGroup,
            owner: str,
            status: str
    ) -> ShareObject:
        with db.scoped_session() as session:
            share = ShareObject(
                datasetUri=dataset.datasetUri,
                environmentUri=environment.environmentUri,
                owner=owner,
                groupUri=env_group.groupUri,
                principalId=env_group.groupUri,
                principalType=PrincipalType.Group.value,
                principalIAMRoleName=env_group.environmentIAMRoleName,
                status=status,
            )
            session.add(share)
            session.commit()

            ResourcePolicy.attach_resource_policy(
                session=session,
                group=env_group.groupUri,
                permissions=SHARE_OBJECT_REQUESTER,
                resource_uri=share.shareUri,
                resource_type=ShareObject.__name__,
            )
            ResourcePolicy.attach_resource_policy(
                session=session,
                group=dataset.SamlAdminGroupName,
                permissions=SHARE_OBJECT_APPROVER,
                resource_uri=share.shareUri,
                resource_type=ShareObject.__name__,
            )
            ResourcePolicy.attach_resource_policy(
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
    return random.choice(
        ['sales', 'finances', 'sites', 'people', 'products', 'partners', 'operations']
    )


def random_tags():
    return [random_tag() for i in range(1, random.choice([2, 3, 4, 5]))]

