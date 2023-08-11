import pytest

from dataall.modules.notebooks.db.models import SagemakerNotebook


class MockSagemakerClient:
    def start_instance(self):
        return "Starting"

    def stop_instance(self):
        return True

    def get_notebook_instance_status(self):
        return "INSERVICE"


@pytest.fixture(scope='module', autouse=True)
def patch_aws(module_mocker):
    module_mocker.patch(
        "dataall.modules.notebooks.services.notebook_service.client",
        return_value=MockSagemakerClient(),
    )


@pytest.fixture(scope='module')
def env_fixture(env, org_fixture, user, group, tenant, module_mocker):
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
