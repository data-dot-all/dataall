import typing
from unittest.mock import MagicMock

import pytest

from dataall.core.environment.db.environment_models import Environment
from dataall.core.organizations.db.organization_models import Organization
from dataall.modules.datasets_base.db.dataset_repositories import DatasetRepository
from dataall.modules.datasets_base.db.dataset_models import DatasetStorageLocation, DatasetTable, Dataset
from tests.core.stacks.test_stack import update_stack_query


@pytest.fixture(scope='module')
def dataset1(
    module_mocker,
    org_fixture: Organization,
    env_fixture: Environment,
    dataset: typing.Callable,
    group,
) -> Dataset:
    kms_client = MagicMock()
    module_mocker.patch(
        'dataall.modules.datasets.services.dataset_service.KmsClient',
        kms_client
    )

    kms_client().get_key_id.return_value = {"some_key"}

    d = dataset(org=org_fixture, env=env_fixture, name='dataset1', owner=env_fixture.owner, group=group.name)
    print(d)
    yield d


def test_get_dataset(client, dataset1, env_fixture, group):
    response = client.query(
        """
        query GetDataset($datasetUri:String!){
            getDataset(datasetUri:$datasetUri){
                label
                AwsAccountId
                description
                region
                imported
                importedS3Bucket
                stewards
                owners
            }
        }
        """,
        datasetUri=dataset1.datasetUri,
        username='alice',
        groups=[group.name],
    )
    assert response.data.getDataset.AwsAccountId == env_fixture.AwsAccountId
    assert response.data.getDataset.region == env_fixture.region
    assert response.data.getDataset.label == 'dataset1'
    assert response.data.getDataset.imported is False
    assert response.data.getDataset.importedS3Bucket is False


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
            'confidentiality': 'Secret',
            'KmsAlias': ''
        },
        groups=[group.name],
    )
    assert response.data.updateDataset.label == 'dataset1updated'
    assert response.data.updateDataset.stewards == group2.name
    assert response.data.updateDataset.confidentiality == 'Secret'

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
            'confidentiality': 'Official',
            'KmsAlias': ''
        },
        groups=[group.name],
    )
    assert response.data.updateDataset.label == 'dataset1updated2'
    assert response.data.updateDataset.stewards == dataset1.SamlAdminGroupName
    assert response.data.updateDataset.confidentiality == 'Official'


def test_start_crawler(org_fixture, env_fixture, dataset1, client, group, module_mocker):
    module_mocker.patch(
        'dataall.modules.datasets.services.dataset_service.DatasetCrawler', MagicMock()
    )
    mutation = """
                mutation StartGlueCrawler($datasetUri:String, $input:CrawlerInput){
                        startGlueCrawler(datasetUri:$datasetUri,input:$input){
                            Name
                            AwsAccountId
                            region
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
    assert response.data.startGlueCrawler.Name == dataset1.GlueCrawlerName


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
        input={
            'label': 'dataset1updated',
            'KmsAlias': ''
        },
    )
    assert 'UnauthorizedOperation' in response.errors[0].message


def test_add_tables(table, dataset1, db):
    for i in range(0, 10):
        table(dataset=dataset1, name=f'table{i+1}', username=dataset1.owner)

    with db.scoped_session() as session:
        nb = session.query(DatasetTable).count()
    assert nb == 10


def test_add_locations(location, dataset1, db):
    for i in range(0, 10):
        location(dataset=dataset1, name=f'unstructured{i+1}', username=dataset1.owner)

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
                        GlueDatabaseName
                        GlueTableName
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
    assert (
        response.data.listDatasetsCreatedInEnvironment.nodes[0].datasetUri
        == dataset1.datasetUri
    )


def test_delete_dataset(client, dataset, env_fixture, org_fixture, db, module_mocker, group, user):
    with db.scoped_session() as session:
        session.query(Dataset).delete()
        session.commit()
    deleted_dataset = dataset(
        org=org_fixture, env=env_fixture, name='dataset1', owner=user.username, group=group.name
    )
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
                AwsAccountId
                description
                region
            }
        }
        """,
        datasetUri=deleted_dataset.datasetUri,
        username=user.username,
        groups=[group.name],
    )
    assert response.data.getDataset is None

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
                AwsAccountId
                region
                imported
                importedS3Bucket
                importedGlueDatabase
                importedKmsKey
                importedAdminRole
                S3BucketName
                GlueDatabaseName
                IAMDatasetAdminRoleArn
                KmsAlias
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
    assert response.data.importDataset.AwsAccountId == env_fixture.AwsAccountId
    assert response.data.importDataset.region == env_fixture.region
    assert response.data.importDataset.imported is True
    assert response.data.importDataset.importedS3Bucket is True
    assert response.data.importDataset.importedGlueDatabase is True
    assert response.data.importDataset.importedKmsKey is True
    assert response.data.importDataset.importedAdminRole is True
    assert response.data.importDataset.S3BucketName == 'dhimportedbucket'
    assert response.data.importDataset.GlueDatabaseName == 'dhimportedGlueDB'
    assert response.data.importDataset.KmsAlias == '1234-YYEY'
    assert 'dhimportedRole' in response.data.importDataset.IAMDatasetAdminRoleArn


def test_get_dataset_by_prefix(db, env_fixture, org_fixture):
    with db.scoped_session() as session:
        dataset = Dataset(
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
        dataset_found: Dataset = DatasetRepository.get_dataset_by_bucket_name(
            session,
            bucket='s3a://insite-data-lake-raw-alpha-eu-west-1/booker/volume_constraints/insite_version=1/volume_constraints.delta'.split(
                '//'
            )[
                1
            ].split(
                '/'
            )[
                0
            ],
        )
        assert dataset_found.S3BucketName == 'insite-data-lake-raw-alpha-eu-west-1'


def test_stewardship(client, dataset, env_fixture, org_fixture, db, group2, group, user, patch_es):
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
