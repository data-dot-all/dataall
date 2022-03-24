import pytest


@pytest.fixture(scope='module')
def org1(org, user, group, tenant):
    org1 = org('testorg', user.userName, group.name)
    yield org1


@pytest.fixture(scope='module')
def env1(env, org1, user, group, tenant, module_mocker):
    module_mocker.patch('requests.post', return_value=True)
    module_mocker.patch(
        'dataall.api.Objects.Environment.resolvers.check_environment', return_value=True
    )
    env1 = env(org1, 'dev', user.userName, group.name, '111111111111', 'eu-west-1')
    yield env1


@pytest.fixture(scope='module', autouse=True)
def pipeline(client, tenant, group, env1):
    response = client.query(
        """
        mutation createSqlPipeline ($input:NewSqlPipelineInput){
            createSqlPipeline(input:$input){
                sqlPipelineUri
                label
                description
                tags
                owner
                repo
                userRoleForPipeline
            }
        }
        """,
        input={
            'label': 'my pipeline',
            'SamlGroupName': group.name,
            'tags': [group.name],
            'environmentUri': env1.environmentUri,
        },
        username='alice',
        groups=[group.name],
    )
    assert response.data.createSqlPipeline.repo
    assert response.data.createSqlPipeline.sqlPipelineUri
    return response.data.createSqlPipeline


def test_update_pipeline(client, tenant, group, pipeline):
    response = client.query(
        """
        mutation updateSqlPipeline ($sqlPipelineUri:String!,$input:UpdateSqlPipelineInput){
            updateSqlPipeline(sqlPipelineUri:$sqlPipelineUri,input:$input){
                sqlPipelineUri
                label
                description
                tags
                owner
                repo
                userRoleForPipeline
            }
        }
        """,
        sqlPipelineUri=pipeline.sqlPipelineUri,
        input={
            'label': 'changed pipeline',
            'tags': [group.name],
        },
        username='alice',
        groups=[group.name],
    )
    assert response.data.updateSqlPipeline.label == 'changed pipeline'


def test_list_pipelines(client, env1, db, org1, user, group, pipeline):
    response = client.query(
        """
        query ListSqlPipelines($filter:SqlPipelineFilter){
            listSqlPipelines(filter:$filter){
                count
                nodes{
                    sqlPipelineUri
                    cloneUrlHttp
                    environment {
                     environmentUri
                    }
                    organization {
                     organizationUri
                    }
                }
            }
        }
        """,
        filter=None,
        username=user.userName,
        groups=[group.name],
    )
    assert len(response.data.listSqlPipelines['nodes']) == 1


def test_nopermissions_pipelines(client, env1, db, org1, user, group, pipeline):
    response = client.query(
        """
        query listSqlPipelines($filter:SqlPipelineFilter){
            listSqlPipelines(filter:$filter){
                count
                nodes{
                    sqlPipelineUri
                }
            }
        }
        """,
        filter=None,
        username='bob',
    )
    assert len(response.data.listSqlPipelines['nodes']) == 0


def test_get_pipeline(client, env1, db, org1, user, group, pipeline, module_mocker):
    module_mocker.patch(
        'dataall.aws.handlers.service_handlers.Worker.process',
        return_value=[{'response': 'return value'}],
    )
    module_mocker.patch(
        'dataall.api.Objects.SqlPipeline.resolvers._get_creds_from_aws',
        return_value=True,
    )
    response = client.query(
        """
        query getSqlPipeline($sqlPipelineUri:String!){
            getSqlPipeline(sqlPipelineUri:$sqlPipelineUri){
                sqlPipelineUri
            }
        }
        """,
        sqlPipelineUri=pipeline.sqlPipelineUri,
        username=user.userName,
        groups=[group.name],
    )
    assert response.data.getSqlPipeline.sqlPipelineUri == pipeline.sqlPipelineUri
    response = client.query(
        """
        query getSqlPipelineCredsLinux($sqlPipelineUri:String!){
            getSqlPipelineCredsLinux(sqlPipelineUri:$sqlPipelineUri)
        }
        """,
        sqlPipelineUri=pipeline.sqlPipelineUri,
        username=user.userName,
        groups=[group.name],
    )
    assert response.data.getSqlPipelineCredsLinux
    response = client.query(
        """
        query browseSqlPipelineRepository($input:SqlPipelineBrowseInput!){
            browseSqlPipelineRepository(input:$input)
        }
        """,
        input=dict(branch='master', sqlPipelineUri=pipeline.sqlPipelineUri),
        username=user.userName,
        groups=[group.name],
    )
    assert response.data.browseSqlPipelineRepository


def test_delete_pipelines(client, env1, db, org1, user, group, module_mocker, pipeline):
    module_mocker.patch(
        'dataall.aws.handlers.service_handlers.Worker.queue', return_value=True
    )
    response = client.query(
        """
        mutation deleteSqlPipeline($sqlPipelineUri:String!,$deleteFromAWS:Boolean){
            deleteSqlPipeline(sqlPipelineUri:$sqlPipelineUri,deleteFromAWS:$deleteFromAWS)
        }
        """,
        sqlPipelineUri=pipeline.sqlPipelineUri,
        deleteFromAWS=True,
        username=user.userName,
        groups=[group.name],
    )
    assert response.data.deleteSqlPipeline
    response = client.query(
        """
        query ListSqlPipelines($filter:SqlPipelineFilter){
            listSqlPipelines(filter:$filter){
                count
                nodes{
                    sqlPipelineUri
                }
            }
        }
        """,
        filter=None,
        username=user.userName,
        groups=[group.name],
    )
    assert len(response.data.listSqlPipelines['nodes']) == 0
