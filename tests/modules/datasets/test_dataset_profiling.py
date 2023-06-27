from unittest.mock import MagicMock

import pytest

from dataall.modules.datasets_base.db.models import DatasetProfilingRun, DatasetTable, Dataset


@pytest.fixture(scope='module', autouse=True)
def org1(org, user, group, tenant):
    org1 = org('testorg', user.userName, group.name)
    yield org1


@pytest.fixture(scope='module', autouse=True)
def env1(env, org1, user, group, tenant):
    env1 = env(org1, 'dev', user.userName, group.name, '111111111111', 'eu-west-1')
    yield env1


@pytest.fixture(scope='module')
def dataset1(env1, org1, dataset, group, user) -> Dataset:
    yield dataset(
        org=org1, env=env1, name='dataset1', owner=user.userName, group=group.name
    )


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


def test_add_tables(table, dataset1, db):
    for i in range(0, 10):
        table(dataset=dataset1, name=f'table{i+1}', username=dataset1.owner)

    with db.scoped_session() as session:
        nb = session.query(DatasetTable).count()
    assert nb == 10


def update_runs(db, runs):
    with db.scoped_session() as session:
        for run in runs:
            run = session.query(DatasetProfilingRun).get(
                run['profilingRunUri']
            )
            run.status = 'SUCCEEDED'
            session.commit()


def test_start_profiling(org1, env1, dataset1, client, module_mocker, db, user, group):
    module_mocker.patch('requests.post', return_value=True)
    module_mocker.patch(
        'dataall.aws.handlers.service_handlers.Worker.process', return_value=True
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
        username=user.userName,
        input={'datasetUri': dataset1.datasetUri, 'GlueTableName': 'table1'},
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


def test_list_runs(client, dataset1, env1, group):
    runs = list_profiling_runs(client, dataset1, group)
    assert len(runs) == 1


def list_profiling_runs(client, dataset1, group):
    response = client.query(
        """
        query listDatasetProfilingRuns($datasetUri:String!){
            listDatasetProfilingRuns(datasetUri:$datasetUri){
                count
                nodes{
                    profilingRunUri
                }
            }
        }
        """,
        datasetUri=dataset1.datasetUri,
        groups=[group.name],
    )
    return response.data.listDatasetProfilingRuns['nodes']


def test_get_table_profiling_run(
    client, dataset1, env1, module_mocker, table, db, group
):
    runs = list_profiling_runs(client, dataset1, group)
    module_mocker.patch(
        'dataall.aws.handlers.service_handlers.Worker.queue',
        return_value=update_runs(db, runs),
    )
    table = table(dataset=dataset1, name='table1', username=dataset1.owner)
    with db.scoped_session() as session:
        table = (
            session.query(DatasetTable)
            .filter(DatasetTable.GlueTableName == 'table1')
            .first()
        )
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
        tableUri=table.tableUri,
        groups=[group.name],
    )
    assert (
        response.data.getDatasetTableProfilingRun['profilingRunUri']
        == runs[0]['profilingRunUri']
    )
    assert response.data.getDatasetTableProfilingRun['status'] == 'SUCCEEDED'
    assert response.data.getDatasetTableProfilingRun['GlueTableName'] == 'table1'


def test_list_table_profiling_runs(
    client, dataset1, env1, module_mocker, table, db, group
):
    module_mocker.patch('requests.post', return_value=True)
    runs = list_profiling_runs(client, dataset1, group)
    table1000 = table(dataset=dataset1, name='table1000', username=dataset1.owner)
    with db.scoped_session() as session:
        table = (
            session.query(DatasetTable)
            .filter(DatasetTable.GlueTableName == 'table1')
            .first()
        )
    module_mocker.patch(
        'dataall.aws.handlers.service_handlers.Worker.queue',
        return_value=update_runs(db, runs),
    )
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
        tableUri=table.tableUri,
        groups=[group.name],
    )
    assert (
        response.data.listDatasetTableProfilingRuns['nodes'][0]['profilingRunUri']
        == runs[0]['profilingRunUri']
    )
    assert (
        response.data.listDatasetTableProfilingRuns['nodes'][0]['status'] == 'SUCCEEDED'
    )
    assert (
        response.data.listDatasetTableProfilingRuns['nodes'][0]['GlueTableName']
        == 'table1'
    )

    module_mocker.patch(
        'dataall.aws.handlers.service_handlers.Worker.queue',
        return_value=update_runs(db, runs),
    )
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
        tableUri=table1000.tableUri,
        groups=[group.name],
    )
    assert response.data.listDatasetTableProfilingRuns['count'] == 0

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
        tableUri=table.tableUri,
        groups=[group.name],
    )
    assert (
        response.data.getDatasetTableProfilingRun['profilingRunUri']
        == runs[0]['profilingRunUri']
    )

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
        tableUri=table1000.tableUri,
    )
    assert not response.data.getDatasetTableProfilingRun
