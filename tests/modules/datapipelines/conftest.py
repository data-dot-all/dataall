import pytest


@pytest.fixture(scope='module')
def env_params(env, org_fixture, user, group, tenant):
    # Overrides the env_fixture environment parameters
    yield {'pipelinesEnabled': 'True'}


@pytest.fixture(scope='module', autouse=True)
def pipeline(client, tenant, group, env_fixture):
    response = client.query(
        """
        mutation createDataPipeline ($input:NewDataPipelineInput!){
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
            'environmentUri': env_fixture.environmentUri,
            'devStrategy': 'trunk',
        },
        username='alice',
        groups=[group.name],
    )
    assert response.data.createDataPipeline.repo
    assert response.data.createDataPipeline.DataPipelineUri
    return response.data.createDataPipeline
