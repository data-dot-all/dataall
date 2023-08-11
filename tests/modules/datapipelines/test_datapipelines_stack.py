import pytest

from dataall.modules.datapipelines.db.models import DataPipeline


@pytest.fixture(scope='module')
def pipeline_env(env, org_fixture, user, group, tenant, module_mocker):
    env1 = env(
        org_fixture,'dev', 'alice', 'testadmins', '111111111111', 'eu-west-1', parameters={'pipelinesEnabled': 'True'}
    )
    yield env1


@pytest.fixture(scope='module')
def pipeline(client, tenant, group, pipeline_env) -> DataPipeline:
    response = client.query(
        """
        mutation createDataPipeline ($input:NewDataPipelineInput){
            createDataPipeline(input:$input){
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
        input={
            'label': 'my pipeline',
            'SamlGroupName': group.name,
            'tags': [group.name],
            'environmentUri': pipeline_env.environmentUri,
            'devStrategy': 'trunk',
        },
        username='alice',
        groups=[group.name],
    )
    yield response.data.createDataPipeline


def test_datapipelines_update_stack_query(client, group, pipeline):
    response = client.query(
        """
        mutation updateStack($targetUri:String!, $targetType:String!){
            updateStack(targetUri:$targetUri, targetType:$targetType){
                stackUri
                targetUri
                name
            }
        }
        """,
        targetUri=pipeline.DataPipelineUri,
        targetType='pipeline',
        username='alice',
        groups=[group.name],
    )
    assert response.data.updateStack.targetUri == pipeline.DataPipelineUri