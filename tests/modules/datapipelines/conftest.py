import pytest


@pytest.fixture(scope='module')
def pipeline_env(env, org_fixture, user, group, tenant):
    env1 = env(
        org_fixture,
        'cicd',
        user.username,
        group.name,
        '111111111111',
        'eu-west-1',
        parameters={'pipelinesEnabled': 'True'}
    )

    yield env1


@pytest.fixture(scope='module', autouse=True)
def pipeline(client, tenant, group, pipeline_env):
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
    assert response.data.createDataPipeline.repo
    assert response.data.createDataPipeline.DataPipelineUri
    return response.data.createDataPipeline
