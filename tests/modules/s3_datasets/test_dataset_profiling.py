from unittest.mock import MagicMock

import pytest

from dataall.modules.s3_datasets.db.dataset_models import DatasetProfilingRun


@pytest.fixture(scope='module', autouse=True)
def org2(org, user2, group2, tenant):
    org2 = org('testorg2', group2, user2)
    yield org2


@pytest.fixture(scope='module', autouse=True)
def env2(env, org2, user2, group2, tenant):
    env2 = env(org2, 'dev2', user2.username, group2.name, '2222222222', 'eu-west-1')
    yield env2


def start_profiling_run(client, dataset, table, user, group):
    dataset.GlueProfilingJobName = ('profile-job',)
    dataset.GlueProfilingTriggerSchedule = ('cron(* 2 * * ? *)',)
    dataset.GlueProfilingTriggerName = ('profile-job',)
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
        input={'datasetUri': dataset.datasetUri, 'GlueTableName': table.name},
        groups=[group.name],
    )
    return response


def test_start_profiling_run_authorized(client, dataset_fixture, table_fixture, db, user, group):
    response = start_profiling_run(client, dataset_fixture, table_fixture, user, group)
    profiling = response.data.startDatasetProfilingRun
    assert profiling.profilingRunUri
    with db.scoped_session() as session:
        profiling = session.query(DatasetProfilingRun).get(profiling.profilingRunUri)
        profiling.GlueJobRunId = 'jr_111111111111'
        session.commit()


def test_start_profiling_run_unauthorized(dataset_fixture, table_fixture, client, db, user2, group2):
    response = start_profiling_run(client, dataset_fixture, table_fixture, user2, group2)
    assert 'UnauthorizedOperation' in response.errors[0].message


def test_get_table_profiling_run_authorized(client, dataset_fixture, table_fixture, db, user, group):
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
        tableUri=table_fixture.tableUri,
        groups=[group.name],
        username=user.username,
    )
    assert response.data.getDatasetTableProfilingRun['profilingRunUri']
    assert response.data.getDatasetTableProfilingRun['status'] == 'RUNNING'
    assert response.data.getDatasetTableProfilingRun['GlueTableName'] == 'table1'


def test_get_table_profiling_run_unauthorized(client, dataset_fixture, table_confidential_fixture, db, user2, group2):
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
        tableUri=table_confidential_fixture.tableUri,
        groups=[group2.name],
        username=user2.username,
    )
    assert 'UnauthorizedOperation' in response.errors[0].message


def test_list_table_profiling_runs_authorized(client, dataset_fixture, table_fixture, db, user, group):
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
        tableUri=table_fixture.tableUri,
        groups=[group.name],
        username=user.username,
    )
    assert response.data.listDatasetTableProfilingRuns['count'] == 1
    assert response.data.listDatasetTableProfilingRuns['nodes'][0]['profilingRunUri']
    assert response.data.listDatasetTableProfilingRuns['nodes'][0]['status'] == 'RUNNING'
    assert response.data.listDatasetTableProfilingRuns['nodes'][0]['GlueTableName'] == 'table1'


def test_list_table_profiling_runs_unauthorized(client, dataset_fixture, table_confidential_fixture, db, user2, group2):
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
        tableUri=table_confidential_fixture.tableUri,
        groups=[group2.name],
        username=user2.username,
    )
    assert 'UnauthorizedOperation' in response.errors[0].message
