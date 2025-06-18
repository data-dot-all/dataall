import typing
from unittest.mock import MagicMock

import pytest

from dataall.base.config import config
from dataall.core.environment.db.environment_models import Environment
from dataall.core.organizations.db.organization_models import Organization
from dataall.modules.s3_datasets.db.dataset_repositories import DatasetRepository
from dataall.modules.s3_datasets.db.dataset_models import DatasetStorageLocation, DatasetTable, S3Dataset
from dataall.modules.datasets_base.db.dataset_models import DatasetBase
from dataall.core.resource_lock.db.resource_lock_models import ResourceLock
from tests.core.stacks.test_stack import update_stack_query

from dataall.modules.datasets_base.services.datasets_enums import ConfidentialityClassification


mocked_key_id = 'some_key'


@pytest.fixture(scope='module', autouse=True)
def mock_s3_client(module_mocker):
    s3_client = MagicMock()
    module_mocker.patch('dataall.modules.s3_datasets.services.dataset_service.S3DatasetClient', s3_client)

    s3_client().get_bucket_encryption.return_value = ('aws:kms', 'key', mocked_key_id)
    yield s3_client


@pytest.fixture(scope='module')
def dataset1(
    module_mocker,
    org_fixture: Organization,
    env_fixture: Environment,
    dataset: typing.Callable,
    group,
) -> S3Dataset:
    kms_client = MagicMock()
    module_mocker.patch('dataall.modules.s3_datasets.services.dataset_service.KmsClient', kms_client)

    kms_client().get_key_id.return_value = mocked_key_id

    d = dataset(org=org_fixture, env=env_fixture, name='dataset1', owner=env_fixture.owner, group=group.name)
    print(d)
    yield d


@pytest.fixture(scope='module')
def dataset2(
    module_mocker,
    org_fixture: Organization,
    env_fixture: Environment,
    dataset: typing.Callable,
    group,
) -> S3Dataset:
    kms_client = MagicMock()
    module_mocker.patch('dataall.modules.s3_datasets.services.dataset_service.KmsClient', kms_client)

    kms_client().get_key_id.return_value = mocked_key_id

    d = dataset(org=org_fixture, env=env_fixture, name='dataset1', owner=env_fixture.owner, group=group.name)
    print(d)
    yield d


def test_get_dataset(client, dataset1, env_fixture, group):
    response = client.query(
        """
        query GetDataset($datasetUri:String!){
            getDataset(datasetUri:$datasetUri){
                label
                description
                stewards
                owners
                imported
                restricted {
                  AwsAccountId
                  region
                  importedS3Bucket
                }
            }
        }
        """,
        datasetUri=dataset1.datasetUri,
        username='alice',
        groups=[group.name],
    )
    assert response.data.getDataset.restricted.AwsAccountId == env_fixture.AwsAccountId
    assert response.data.getDataset.restricted.region == env_fixture.region
    assert response.data.getDataset.label == 'dataset1'
    assert response.data.getDataset.imported is False
    assert response.data.getDataset.restricted.importedS3Bucket is False


def test_list_datasets(client, dataset1, group):
    response = client.query(
        """
        query ListDatasets($filter:DatasetFilter){
            listDatasets(filter:$filter){
                count
                nodes{
                    datasetUri
                    label
                }
            }
        }
        """,
        filter=None,
        username='alice',
        groups=[group.name],
    )
    assert response.data.listDatasets.count == 1
    assert response.data.listDatasets.nodes[0].datasetUri == dataset1.datasetUri


def test_update_dataset(dataset1, client, group, group2, module_mocker):
    response = client.query(
        """
        mutation UpdateDataset($datasetUri:String!,$input:ModifyDatasetInput){
            updateDataset(datasetUri:$datasetUri,input:$input){
                datasetUri
                label
                tags
                stewards
                confidentiality
            }
        }
        """,
        username=dataset1.owner,
        datasetUri=dataset1.datasetUri,
        input={
            'label': 'dataset1updated',
            'stewards': group2.name,
            'confidentiality': ConfidentialityClassification.Secret.value,
            'KmsAlias': '',
        },
        groups=[group.name],
    )
    assert response.data.updateDataset.label == 'dataset1updated'
    assert response.data.updateDataset.stewards == group2.name
    assert response.data.updateDataset.confidentiality == ConfidentialityClassification.Secret.value

    response = client.query(
        """
        query ListDatasets($filter:DatasetFilter){
            listDatasets(filter:$filter){
                count
                nodes{
                    datasetUri
                    label
                    userRoleForDataset
                }
            }
        }
        """,
        filter=None,
        username='steward',
        groups=[group2.name],
    )
    assert response.data.listDatasets.count == 1
    assert response.data.listDatasets.nodes[0].datasetUri == dataset1.datasetUri

    response = client.query(
        """
        mutation UpdateDataset($datasetUri:String!,$input:ModifyDatasetInput){
            updateDataset(datasetUri:$datasetUri,input:$input){
                datasetUri
                label
                tags
                stewards
                confidentiality
            }
        }
        """,
        username=dataset1.owner,
        datasetUri=dataset1.datasetUri,
        input={
            'label': 'dataset1updated2',
            'stewards': dataset1.SamlAdminGroupName,
            'confidentiality': ConfidentialityClassification.Official.value,
            'KmsAlias': '',
        },
        groups=[group.name],
    )
    assert response.data.updateDataset.label == 'dataset1updated2'
    assert response.data.updateDataset.stewards == dataset1.SamlAdminGroupName
    assert response.data.updateDataset.confidentiality == ConfidentialityClassification.Official.value


@pytest.mark.skipif(
    not config.get_property('modules.s3_datasets.features.glue_crawler'), reason='Feature Disabled by Config'
)
def test_start_crawler(org_fixture, env_fixture, dataset1, client, group, module_mocker):
    module_mocker.patch('dataall.modules.s3_datasets.services.dataset_service.DatasetCrawler', MagicMock())
    mutation = """
                mutation StartGlueCrawler($datasetUri:String, $input:CrawlerInput){
                        startGlueCrawler(datasetUri:$datasetUri,input:$input){
                            Name
                            status
                        }
                    }
                """
    response = client.query(
        mutation,
        datasetUri=dataset1.datasetUri,
        username=dataset1.owner,
        groups=[group.name],
        input={
            'prefix': 'raw',
        },
    )
    assert response.data.Name == dataset1.restricted.GlueCrawlerName


def test_update_dataset_unauthorized(dataset1, client, group):
    response = client.query(
        """
        mutation UpdateDataset($datasetUri:String!,$input:ModifyDatasetInput){
            updateDataset(datasetUri:$datasetUri,input:$input){
                datasetUri
                label
                tags
            }
        }
        """,
        username='anonymoususer',
        datasetUri=dataset1.datasetUri,
        input={'label': 'dataset1updated', 'KmsAlias': ''},
    )
    assert 'UnauthorizedOperation' in response.errors[0].message


def test_add_tables(table, dataset1, db):
    for i in range(0, 10):
        table(dataset=dataset1, name=f'table{i + 1}', username=dataset1.owner)

    with db.scoped_session() as session:
        nb = session.query(DatasetTable).count()
    assert nb == 10


def test_add_locations(location, dataset1, db):
    for i in range(0, 10):
        location(dataset=dataset1, name=f'unstructured{i + 1}', username=dataset1.owner)

    with db.scoped_session() as session:
        nb = session.query(DatasetStorageLocation).count()
    assert nb == 10


def test_list_dataset_locations(client, dataset1, group):
    q = """
        query GetDataset($datasetUri:String!,$lFilter:DatasetStorageLocationFilter){
            getDataset(datasetUri:$datasetUri){
                datasetUri
                locations(filter:$lFilter){
                    count
                    nodes{
                        locationUri
                        name
                        label
                        S3Prefix
                    }
                }
            }
        }
    """
    response = client.query(
        q,
        username=dataset1.owner,
        groups=[group.name],
        datasetUri=dataset1.datasetUri,
        lFilter={'pageSize': 100},
    )
    print(response)
    assert response.data.getDataset.locations.count == 10
    assert len(response.data.getDataset.locations.nodes) == 10

    response = client.query(
        q,
        username=dataset1.owner,
        groups=[group.name],
        datasetUri=dataset1.datasetUri,
        lFilter={'pageSize': 3},
    )
    assert response.data.getDataset.locations.count == 10
    assert len(response.data.getDataset.locations.nodes) == 3

    response = client.query(
        q,
        username=dataset1.owner,
        groups=[group.name],
        datasetUri=dataset1.datasetUri,
        lFilter={'pageSize': 100, 'term': 'unstructured2'},
    )
    print(response)
    assert response.data.getDataset.locations.count == 1
    assert len(response.data.getDataset.locations.nodes) == 1


def test_list_dataset_tables(client, dataset1, group):
    q = """
        query GetDataset($datasetUri:String!,$tableFilter:DatasetTableFilter){
            getDataset(datasetUri:$datasetUri){
                datasetUri
                tables(filter:$tableFilter){
                    count
                    nodes{
                        tableUri
                        name
                        label
                        restricted{
                            GlueDatabaseName
                            GlueTableName
                            S3Prefix
                        }
                    }
                }
            }
        }
    """
    response = client.query(
        q,
        username=dataset1.owner,
        groups=[group.name],
        datasetUri=dataset1.datasetUri,
        tableFilter={'pageSize': 100},
    )
    assert response.data.getDataset.tables.count == 10
    assert len(response.data.getDataset.tables.nodes) == 10

    response = client.query(
        q,
        username=dataset1.owner,
        groups=[group.name],
        datasetUri=dataset1.datasetUri,
        tableFilter={'pageSize': 3},
    )
    assert response.data.getDataset.tables.count == 10
    assert len(response.data.getDataset.tables.nodes) == 3

    response = client.query(
        q,
        username=dataset1.owner,
        groups=[group.name],
        datasetUri=dataset1.datasetUri,
        tableFilter={'pageSize': 100, 'term': 'table1'},
    )
    assert response.data.getDataset.tables.count == 2
    assert len(response.data.getDataset.tables.nodes) == 2


def test_dataset_in_environment(client, env_fixture, dataset1, group):
    q = """
    query ListDatasetsCreatedInEnvironment($environmentUri:String!){
        listDatasetsCreatedInEnvironment(environmentUri:$environmentUri){
            count
            nodes{
                datasetUri
            }
        }
    }
    """
    response = client.query(
        q, username=env_fixture.owner, groups=[group.name], environmentUri=env_fixture.environmentUri
    )
    assert response.data.listDatasetsCreatedInEnvironment.count == 1
    assert response.data.listDatasetsCreatedInEnvironment.nodes[0].datasetUri == dataset1.datasetUri


def test_delete_dataset(client, dataset, env_fixture, org_fixture, db, module_mocker, group, user):
    # Delete any Dataset before effectuating the test
    with db.scoped_session() as session:
        session.query(ResourceLock).delete()
        session.query(S3Dataset).delete()
        session.query(DatasetBase).delete()
        session.commit()
    deleted_dataset = dataset(org=org_fixture, env=env_fixture, name='dataset1', owner=user.username, group=group.name)
    response = client.query(
        """
        mutation deleteDataset($datasetUri:String!,$deleteFromAWS:Boolean){
            deleteDataset(datasetUri:$datasetUri, deleteFromAWS:$deleteFromAWS)
        }
        """,
        datasetUri=deleted_dataset.datasetUri,
        deleteFromAWS=True,
        username=user.username,
        groups=[group.name],
    )
    assert response
    response = client.query(
        """
        query GetDataset($datasetUri:String!){
            getDataset(datasetUri:$datasetUri){
                label
                restricted {
                    AwsAccountId
                    region
                }
                description
            }
        }
        """,
        datasetUri=deleted_dataset.datasetUri,
        username=user.username,
        groups=[group.name],
    )
    assert response.data.getDataset == None

    response = client.query(
        """
        query ListDatasets($filter:DatasetFilter){
            listDatasets(filter:$filter){
                count
                nodes{
                    datasetUri
                    label
                }
            }
        }
        """,
        filter=None,
        username=user.username,
        groups=[group.name],
    )
    assert response.data.listDatasets.count == 0


def test_import_dataset(org_fixture, env_fixture, dataset1, client, group):
    response = client.query(
        """
        mutation importDataset($input:ImportDatasetInput){
            importDataset(input:$input){
                label
                imported
                restricted {
                    AwsAccountId
                    region
                    S3BucketName
                    GlueDatabaseName
                    IAMDatasetAdminRoleArn
                    KmsAlias
                }
            }
        }
        """,
        username=dataset1.owner,
        groups=[group.name],
        input={
            'organizationUri': org_fixture.organizationUri,
            'environmentUri': env_fixture.environmentUri,
            'label': 'datasetImported',
            'bucketName': 'dhimportedbucket',
            'glueDatabaseName': 'dhimportedGlueDB',
            'adminRoleName': 'dhimportedRole',
            'KmsKeyAlias': '1234-YYEY',
            'owner': dataset1.owner,
            'SamlAdminGroupName': group.name,
        },
    )
    assert response.data.importDataset.label == 'datasetImported'
    assert response.data.importDataset.restricted.AwsAccountId == env_fixture.AwsAccountId
    assert response.data.importDataset.restricted.region == env_fixture.region
    assert response.data.importDataset.imported is True
    assert response.data.importDataset.restricted.S3BucketName == 'dhimportedbucket'
    assert response.data.importDataset.restricted.GlueDatabaseName == 'dhimportedGlueDB'
    assert response.data.importDataset.restricted.KmsAlias == '1234-YYEY'
    assert 'dhimportedRole' in response.data.importDataset.restricted.IAMDatasetAdminRoleArn


def test_get_dataset_by_prefix(db, env_fixture, org_fixture):
    with db.scoped_session() as session:
        dataset = S3Dataset(
            label='thisdataset',
            environmentUri=env_fixture.environmentUri,
            organizationUri=org_fixture.organizationUri,
            name='thisdataset',
            description='test',
            AwsAccountId=env_fixture.AwsAccountId,
            region=env_fixture.region,
            S3BucketName='insite-data-lake-raw-alpha-eu-west-1',
            GlueDatabaseName='db',
            IAMDatasetAdminRoleArn='role',
            IAMDatasetAdminUserArn='xxx',
            KmsAlias='xxx',
            owner='me',
            confidentiality='C1',
            businessOwnerEmail='jeff',
            businessOwnerDelegationEmails=['andy'],
            SamlAdminGroupName='admins',
        )
        session.add(dataset)
        session.commit()
        dataset_found: S3Dataset = DatasetRepository.get_dataset_by_bucket_name(
            session,
            bucket='s3a://insite-data-lake-raw-alpha-eu-west-1/booker/volume_constraints/insite_version=1/volume_constraints.delta'.split(
                '//'
            )[1].split('/')[0],
        )
        assert dataset_found.S3BucketName == 'insite-data-lake-raw-alpha-eu-west-1'


def test_stewardship(client, dataset, env_fixture, org_fixture, db, group2, group, user, patch_es):
    response = client.query(
        """
        mutation CreateDataset($input:NewDatasetInput!){
            createDataset(
            input:$input
            ){
                datasetUri
                label
                description
                restricted {
                  AwsAccountId
                  region
                  KmsAlias
                  S3BucketName
                  GlueDatabaseName
                  IAMDatasetAdminRoleArn
                }
                owner
                SamlAdminGroupName
                stewards

            }
        }
        """,
        username=user.username,
        groups=[group.name],
        input={
            'owner': user.username,
            'label': f'stewardsds',
            'description': 'test dataset {name}',
            'businessOwnerEmail': 'jeff@amazon.com',
            'tags': ['t1', 't2'],
            'environmentUri': env_fixture.environmentUri,
            'SamlAdminGroupName': group.name,
            'stewards': group2.name,
            'organizationUri': org_fixture.organizationUri,
        },
    )
    assert response.data.createDataset.stewards == group2.name


def test_dataset_stack(client, dataset_fixture, group):
    dataset = dataset_fixture
    response = update_stack_query(client, dataset.datasetUri, 'dataset', dataset.SamlAdminGroupName)
    assert response.data.updateStack.targetUri == dataset.datasetUri


def test_create_dataset_with_expiration_setting(client, env_fixture, org_fixture, db, group2, group, user, patch_es):
    response = client.query(
        """
        mutation CreateDataset($input:NewDatasetInput!){
            createDataset(
            input:$input
            ){
                enableExpiration
                expirySetting
                expiryMinDuration
                expiryMaxDuration
            }
        }
        """,
        username=user.username,
        groups=[group.name],
        input={
            'owner': user.username,
            'label': f'stewardsds',
            'description': 'test dataset {name}',
            'businessOwnerEmail': 'jeff@amazon.com',
            'tags': ['t1', 't2'],
            'environmentUri': env_fixture.environmentUri,
            'SamlAdminGroupName': group.name,
            'stewards': group2.name,
            'organizationUri': org_fixture.organizationUri,
            'enableExpiration': True,
            'expirySetting': 'Monthly',
            'expiryMinDuration': 1,
            'expiryMaxDuration': 3,
        },
    )

    assert response.data.createDataset.enableExpiration == True
    assert response.data.createDataset.expirySetting == 'Monthly'
    assert response.data.createDataset.expiryMinDuration == 1
    assert response.data.createDataset.expiryMaxDuration == 3


def test_update_dataset_with_expiration_setting_changes(dataset2, client, user, group, group2):
    assert dataset2.enableExpiration == False
    assert dataset2.expirySetting == None
    assert dataset2.expiryMinDuration == None
    assert dataset2.expiryMaxDuration == None

    response = client.query(
        """
        mutation UpdateDataset($datasetUri:String!,$input:ModifyDatasetInput){
            updateDataset(datasetUri:$datasetUri,input:$input){
                datasetUri
                label
                tags
                stewards
                confidentiality
                enableExpiration
                expirySetting
                expiryMinDuration
                expiryMaxDuration
            }
        }
        """,
        username=user.username,
        datasetUri=dataset2.datasetUri,
        input={
            'label': 'dataset1updated',
            'stewards': group2.name,
            'confidentiality': ConfidentialityClassification.Secret.value,
            'KmsAlias': '',
            'enableExpiration': True,
            'expirySetting': 'Monthly',
            'expiryMinDuration': 1,
            'expiryMaxDuration': 3,
        },
        groups=[group.name],
    )

    assert response.data.updateDataset.enableExpiration == True
    assert response.data.updateDataset.expirySetting == 'Monthly'
    assert response.data.updateDataset.expiryMinDuration == 1
    assert response.data.updateDataset.expiryMaxDuration == 3


def test_update_dataset_with_expiration_with_incorrect_input(dataset2, client, group, group2):
    assert dataset2.enableExpiration == False
    assert dataset2.expirySetting == None
    assert dataset2.expiryMinDuration == None
    assert dataset2.expiryMaxDuration == None

    response = client.query(
        """
        mutation UpdateDataset($datasetUri:String!,$input:ModifyDatasetInput){
            updateDataset(datasetUri:$datasetUri,input:$input){
                datasetUri
                label
                tags
                stewards
                confidentiality
                enableExpiration
                expirySetting
                expiryMinDuration
                expiryMaxDuration
            }
        }
        """,
        username=dataset2.owner,
        datasetUri=dataset2.datasetUri,
        input={
            'label': 'dataset1updated',
            'stewards': group2.name,
            'confidentiality': ConfidentialityClassification.Secret.value,
            'KmsAlias': '',
            'enableExpiration': True,
            'expirySetting': 'SOMETHING',
            'expiryMinDuration': 1,
            'expiryMaxDuration': 3,
        },
        groups=[group.name],
    )

    assert 'InvalidInput' in response.errors[0].message
    assert 'Expiration Setting value SOMETHING must be is of invalid type' in response.errors[0].message

    response = client.query(
        """
        mutation UpdateDataset($datasetUri:String!,$input:ModifyDatasetInput){
            updateDataset(datasetUri:$datasetUri,input:$input){
                datasetUri
                label
                tags
                stewards
                confidentiality
                enableExpiration
                expirySetting
                expiryMinDuration
                expiryMaxDuration
            }
        }
        """,
        username=dataset2.owner,
        datasetUri=dataset2.datasetUri,
        input={
            'label': 'dataset1updated',
            'stewards': group2.name,
            'confidentiality': ConfidentialityClassification.Secret.value,
            'KmsAlias': '',
            'enableExpiration': True,
            'expirySetting': 'Monthly',
            'expiryMinDuration': -1,
            'expiryMaxDuration': 3,
        },
        groups=[group.name],
    )

    assert 'InvalidInput' in response.errors[0].message
    assert 'expiration duration  value  must be must be greater than zero' in response.errors[0].message


def test_import_dataset_with_expiration_setting(org_fixture, env_fixture, dataset1, client, group):
    response = client.query(
        """
        mutation importDataset($input:ImportDatasetInput){
            importDataset(input:$input){
                enableExpiration
                expirySetting
                expiryMinDuration
                expiryMaxDuration
            }
        }
        """,
        username=dataset1.owner,
        groups=[group.name],
        input={
            'organizationUri': org_fixture.organizationUri,
            'environmentUri': env_fixture.environmentUri,
            'label': 'datasetImportedin',
            'bucketName': 'dhimportedbucketin',
            'glueDatabaseName': 'dhimportedGlueDBin',
            'adminRoleName': 'dhimportedRolein',
            'KmsKeyAlias': '1234-YYEY-888',
            'owner': dataset1.owner,
            'SamlAdminGroupName': group.name,
            'enableExpiration': True,
            'expirySetting': 'Monthly',
            'expiryMinDuration': 1,
            'expiryMaxDuration': 3,
        },
    )
    assert response.data.importDataset.enableExpiration == True
    assert response.data.importDataset.expirySetting == 'Monthly'
    assert response.data.importDataset.expiryMinDuration == 1
    assert response.data.importDataset.expiryMaxDuration == 3
