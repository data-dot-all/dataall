from dataall.modules.notebooks.db.models import SagemakerNotebook
from tests.client import client
from tests.core.conftest import *


@pytest.fixture(scope='module')
def env_fixture(env, org_fixture, user, group, tenant, module_mocker):
    module_mocker.patch('requests.post', return_value=True)
    module_mocker.patch('dataall.core.environment.api.resolvers.check_environment', return_value=True)
    env1 = env(org_fixture, 'dev', 'alice', 'testadmins', '111111111111', 'eu-west-1',
               parameters={'notebooksEnabled': 'True'})
    yield env1


@pytest.fixture(scope='module')
def sgm_notebook(client, tenant, group, env_fixture) -> SagemakerNotebook:
    response = client.query(
        """
        mutation createSagemakerNotebook($input:NewSagemakerNotebookInput){
            createSagemakerNotebook(input:$input){
                notebookUri
                label
                description
                tags
                owner
                userRoleForNotebook
                SamlAdminGroupName
                VpcId
                SubnetId
                VolumeSizeInGB
                InstanceType
            }
        }
        """,
        input={
            'label': 'my best notebook ever',
            'SamlAdminGroupName': group.name,
            'tags': [group.name],
            'environmentUri': env_fixture.environmentUri,
            'VpcId': 'vpc-123567',
            'SubnetId': 'subnet-123567',
            'VolumeSizeInGB': 32,
            'InstanceType': 'ml.m5.xlarge',
        },
        username='alice',
        groups=[group.name],
    )
    yield response.data.createSagemakerNotebook
