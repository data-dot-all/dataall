import pytest


def test_create_pipeline_environment(client, tenant, group, env_fixture, pipeline):
    response = client.query(
        """
        mutation createDataPipelineEnvironment($input: NewDataPipelineEnvironmentInput!) {
          createDataPipelineEnvironment(input: $input) {
            envPipelineUri
            environmentUri
            environmentLabel
            pipelineUri
            pipelineLabel
            stage
            region
            AwsAccountId
            samlGroupName
          }
        }
        """,
        input={
            'stage': 'dev',
            'order': 1,
            'pipelineUri': pipeline.DataPipelineUri,
            'environmentUri': env_fixture.environmentUri,
            'environmentLabel': env_fixture.label,
            'samlGroupName': group.name,
        },
        username='alice',
        groups=[group.name],
    )
    assert response.data.createDataPipelineEnvironment.envPipelineUri
    assert response.data.createDataPipelineEnvironment.stage == 'dev'
    assert response.data.createDataPipelineEnvironment.AwsAccountId == env_fixture.AwsAccountId


def test_update_pipeline(client, tenant, group, pipeline):
    response = client.query(
        """
        mutation updateDataPipeline ($DataPipelineUri:String!,$input:UpdateDataPipelineInput){
            updateDataPipeline(DataPipelineUri:$DataPipelineUri,input:$input){
                DataPipelineUri
                label
                description
                tags
                owner
                repo
                userRoleForPipeline
            }
        }
        """,
        DataPipelineUri=pipeline.DataPipelineUri,
        input={
            'label': 'changed pipeline',
            'tags': [group.name],
        },
        username='alice',
        groups=[group.name],
    )
    assert response.data.updateDataPipeline.label == 'changed pipeline'


def test_list_pipelines(client, env_fixture, db, user, group, pipeline):
    response = client.query(
        """
        query ListDataPipelines($filter:DataPipelineFilter){
            listDataPipelines(filter:$filter){
                count
                nodes{
                    DataPipelineUri
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
        username=user.username,
        groups=[group.name],
    )
    assert len(response.data.listDataPipelines['nodes']) == 1


def test_nopermissions_pipelines(client, env_fixture, db, user, group, pipeline):
    response = client.query(
        """
        query listDataPipelines($filter:DataPipelineFilter){
            listDataPipelines(filter:$filter){
                count
                nodes{
                    DataPipelineUri
                }
            }
        }
        """,
        filter=None,
        username='bob',
    )
    assert len(response.data.listDataPipelines['nodes']) == 0


def test_get_pipeline(client, env_fixture, db, user, group, pipeline, module_mocker):
    module_mocker.patch(
        'dataall.modules.datapipelines.services.datapipelines_service.DataPipelineService._get_credentials_from_aws',
        return_value=True,
    )
    response = client.query(
        """
        query getDataPipeline($DataPipelineUri:String!){
            getDataPipeline(DataPipelineUri:$DataPipelineUri){
                DataPipelineUri
            }
        }
        """,
        DataPipelineUri=pipeline.DataPipelineUri,
        username=user.username,
        groups=[group.name],
    )
    assert response.data.getDataPipeline.DataPipelineUri == pipeline.DataPipelineUri
    response = client.query(
        """
        query getDataPipelineCredsLinux($DataPipelineUri:String!){
            getDataPipelineCredsLinux(DataPipelineUri:$DataPipelineUri)
        }
        """,
        DataPipelineUri=pipeline.DataPipelineUri,
        username=user.username,
        groups=[group.name],
    )
    assert response.data.getDataPipelineCredsLinux


def test_delete_pipelines(client, env_fixture, db, user, group, pipeline):
    response = client.query(
        """
        mutation deleteDataPipeline($DataPipelineUri:String!,$deleteFromAWS:Boolean){
            deleteDataPipeline(DataPipelineUri:$DataPipelineUri,deleteFromAWS:$deleteFromAWS)
        }
        """,
        DataPipelineUri=pipeline.DataPipelineUri,
        deleteFromAWS=True,
        username=user.username,
        groups=[group.name],
    )
    assert response.data.deleteDataPipeline
    response = client.query(
        """
        query ListDataPipelines($filter:DataPipelineFilter){
            listDataPipelines(filter:$filter){
                count
                nodes{
                    DataPipelineUri
                }
            }
        }
        """,
        filter=None,
        username=user.username,
        groups=[group.name],
    )
    assert len(response.data.listDataPipelines['nodes']) == 0
