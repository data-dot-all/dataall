import pytest

from dataall.modules.mlstudio.db.models import SagemakerStudioUser
from tests.api.client import client, app
from tests.api.conftest import *


@pytest.fixture(scope='module', autouse=True)
def patch_aws(module_mocker):
    module_mocker.patch('requests.post', return_value=True)
    module_mocker.patch(
        'dataall.aws.handlers.service_handlers.Worker.queue', return_value=True
    )

@pytest.fixture(scope='module', autouse=True)
def patch_aws_sagemaker_client(module_mocker):
    module_mocker.patch(
        'dataall.modules.mlstudio.services.mlstudio_service.get_sagemaker_studio_domain',
        return_value={'DomainId': 'test'},
    )



@pytest.fixture(scope='module')
def env_fixture(env, org_fixture, user, group, tenant, module_mocker):
    module_mocker.patch('requests.post', return_value=True)
    module_mocker.patch('dataall.api.Objects.Environment.resolvers.check_environment', return_value=True)
    env1 = env(org_fixture, 'dev', 'alice', 'testadmins', '111111111111', 'eu-west-1',
               parameters={'mlStudiosEnabled': 'True'})
    yield env1


@pytest.fixture(scope='module')
def sagemaker_studio_user(client, tenant, group, env_fixture) -> SagemakerStudioUser:
    response = client.query(
        """
            mutation createSagemakerStudioUser($input:NewSagemakerStudioUserInput){
            createSagemakerStudioUser(input:$input){
                sagemakerStudioUserUri
                name
                label
                created
                description
                SamlAdminGroupName
                environmentUri
                tags
            }
        }
            """,
        input={
            'label': 'testcreate',
            'SamlAdminGroupName': group.name,
            'environmentUri': env_fixture.environmentUri,
        },
        username='alice',
        groups=[group.name],
    )
    yield response.data.createSagemakerStudioUser

@pytest.fixture(scope='module')
def multiple_sagemaker_studio_users(client, db, env_fixture, group):
        for i in range(0, 10):
            response = client.query(
                """
                mutation createSagemakerStudioUser($input:NewSagemakerStudioUserInput){
                createSagemakerStudioUser(input:$input){
                    sagemakerStudioUserUri
                    name
                    label
                    created
                    description
                    SamlAdminGroupName
                    environmentUri
                    tags
                }
            }
                """,
                input={
                    'label': f'test{i}',
                    'SamlAdminGroupName': group.name,
                    'environmentUri': env_fixture.environmentUri,
                },
                username='alice',
                groups=[group.name],
            )
            assert response.data.createSagemakerStudioUser.label == f'test{i}'
            assert (
                    response.data.createSagemakerStudioUser.SamlAdminGroupName
                    == group.name
            )
            assert (
                    response.data.createSagemakerStudioUser.environmentUri
                    == env_fixture.environmentUri
            )
