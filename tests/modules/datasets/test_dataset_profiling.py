from unittest.mock import MagicMock

import pytest

from dataall.core.permissions.db.resource_policy import ResourcePolicy
from dataall.modules.datasets.api.dataset.enums import ConfidentialityClassification
from dataall.modules.datasets_base.db.models import DatasetProfilingRun, Dataset, DatasetTable
from dataall.modules.datasets_base.services.permissions import DATASET_TABLE_READ


@pytest.fixture(scope='module', autouse=True)
def org1(org, user, group, tenant):
    org1 = org('testorg', user.username, group.name)
    yield org1


@pytest.fixture(scope='module', autouse=True)
def env1(env, org1, user, group, tenant):
    env1 = env(org1, 'dev', user.username, group.name, '111111111111', 'eu-west-1')
    yield env1


@pytest.fixture(scope='module', autouse=True)
def org2(org, user2, group2, tenant):
    org2 = org('testorg2', user2.username, group2.name)
    yield org2


@pytest.fixture(scope='module', autouse=True)
def env2(env, org2, user2, group2, tenant):
    env2 = env(org2, 'dev2', user2.username, group2.name, '2222222222', 'eu-west-1')
    yield env2


@pytest.fixture(scope='module')
def dataset1(env1, org1, dataset, group, user) -> Dataset:
    dataset1 = dataset(
        org=org1, env=env1, name='dataset1', owner=user.username, group=group.name,
        confidentiality=ConfidentialityClassification.Secret.value
    )
    yield dataset1


@pytest.fixture(scope='module', autouse=True)
def patch_methods(module_mocker):
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


@pytest.fixture(scope='module')
def table1(db, dataset1, table, group, user):
    table1 = table(dataset=dataset1, name="table1", username=user.username)

    with db.scoped_session() as session:
        ResourcePolicy.attach_resource_policy(
            session=session,
            group=group.groupUri,
            permissions=DATASET_TABLE_READ,
            resource_uri=table1.tableUri,
            resource_type=DatasetTable.__name__,
        )
    return table1


def test_start_profiling_run_authorized(org1, env1, dataset1, table1, client, module_mocker, db, user, group):
    module_mocker.patch('requests.post', return_value=True)
    module_mocker.patch(
        'dataall.core.tasks.service_handlers.Worker.process', return_value=True
    )
    dataset1.GlueProfilingJobName = ('profile-job',)
    dataset1.GlueProfilingTriggerSchedule = ('cron(* 2 * * ? *)',)
    dataset1.GlueProfilingTriggerName = ('profile-job',)
    response = client.query(
        """
        mutation startDatasetProfilingRun($input:StartDatasetProfilingRunInput){
            startDatasetProfilingRun(input:$input)
                {
                    profilingRunUri
                }
            }
        """,
        username=user.username,
        input={'datasetUri': dataset1.datasetUri, 'GlueTableName': table1.name},
        groups=[group.name],
    )
    profiling = response.data.startDatasetProfilingRun
    assert profiling.profilingRunUri
    with db.scoped_session() as session:
        profiling = session.query(DatasetProfilingRun).get(
            profiling.profilingRunUri
        )
        profiling.GlueJobRunId = 'jr_111111111111'
        session.commit()


def test_start_profiling_run_unauthorized(org2, env2, dataset1, table1, client, module_mocker, db, user2, group2):
    module_mocker.patch('requests.post', return_value=True)
    module_mocker.patch(
        'dataall.core.tasks.service_handlers.Worker.process', return_value=True
    )
    dataset1.GlueProfilingJobName = ('profile-job',)
    dataset1.GlueProfilingTriggerSchedule = ('cron(* 2 * * ? *)',)
    dataset1.GlueProfilingTriggerName = ('profile-job',)
    response = client.query(
        """
        mutation startDatasetProfilingRun($input:StartDatasetProfilingRunInput){
            startDatasetProfilingRun(input:$input)
                {
                    profilingRunUri
                }
            }
        """,
        username=user2.username,
        input={'datasetUri': dataset1.datasetUri, 'GlueTableName': table1.name},
        groups=[group2.name],
    )
    assert 'UnauthorizedOperation' in response.errors[0].message


def test_get_table_profiling_run_authorized(
    client, dataset1, table1, db, user, group
):
    response = client.query(
        """
        query getDatasetTableProfilingRun($tableUri:String!){
            getDatasetTableProfilingRun(tableUri:$tableUri){
                profilingRunUri
                status
                GlueTableName
            }
        }
        """,
        tableUri=table1.tableUri,
        groups=[group.name],
        username=user.username,
    )
    assert response.data.getDatasetTableProfilingRun['profilingRunUri']
    assert response.data.getDatasetTableProfilingRun['status'] == 'RUNNING'
    assert response.data.getDatasetTableProfilingRun['GlueTableName'] == 'table1'


def test_get_table_profiling_run_unauthorized(
    client, dataset1, module_mocker, table1, db, user2, group2
):
    response = client.query(
        """
        query getDatasetTableProfilingRun($tableUri:String!){
            getDatasetTableProfilingRun(tableUri:$tableUri){
                profilingRunUri
                status
                GlueTableName
            }
        }
        """,
        tableUri=table1.tableUri,
        groups=[group2.name],
        username=user2.username,
    )
    assert 'UnauthorizedOperation' in response.errors[0].message


def test_list_table_profiling_runs_authorized(
    client, dataset1, module_mocker, table1, db, user, group
):
    module_mocker.patch('requests.post', return_value=True)

    response = client.query(
        """
        query listDatasetTableProfilingRuns($tableUri:String!){
            listDatasetTableProfilingRuns(tableUri:$tableUri){
                count
                nodes{
                    profilingRunUri
                    status
                    GlueTableName
                }

            }
        }
        """,
        tableUri=table1.tableUri,
        groups=[group.name],
        username=user.username,
    )
    assert response.data.listDatasetTableProfilingRuns['count'] == 1
    assert response.data.listDatasetTableProfilingRuns['nodes'][0]['profilingRunUri']
    assert (
        response.data.listDatasetTableProfilingRuns['nodes'][0]['status'] == 'RUNNING'
    )
    assert (
        response.data.listDatasetTableProfilingRuns['nodes'][0]['GlueTableName']
        == 'table1'
    )


def test_list_table_profiling_runs_unauthorized(
    client, dataset1, module_mocker, table1, db, user2, group2
):
    module_mocker.patch('requests.post', return_value=True)

    response = client.query(
        """
        query listDatasetTableProfilingRuns($tableUri:String!){
            listDatasetTableProfilingRuns(tableUri:$tableUri){
                count
                nodes{
                    profilingRunUri
                    status
                    GlueTableName
                }

            }
        }
        """,
        tableUri=table1.tableUri,
        groups=[group2.name],
        username=user2.username,
    )
    assert 'UnauthorizedOperation' in response.errors[0].message
