import pytest

from dataall.modules.mlstudio.db.models import SagemakerStudioUser
from tests.api.client import client, app
from tests.api.conftest import *

@pytest.fixture(scope='module')
def env_fixture(env, org_fixture, user, group, tenant, module_mocker):
    module_mocker.patch('requests.post', return_value=True)
    module_mocker.patch('dataall.api.Objects.Environment.resolvers.check_environment', return_value=True)
    env1 = env(org_fixture, 'dev', 'alice', 'testadmins', '111111111111', 'eu-west-1',
               parameters={'mlstudioEnabled': 'True'})
    yield env1


@pytest.fixture(scope='module')
def sagemaker_studio_user(client, tenant, group, env_fixture, module_mocker) -> SagemakerStudioUser:
    module_mocker.patch(
        'dataall.aws.handlers.sagemaker_studio.SagemakerStudio.get_sagemaker_studio_domain',
        return_value={'DomainId': 'test'},
    )
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

def multiple_sagemaker_studio_users(client, db, env1, group, module_mocker):
        module_mocker.patch(
            'dataall.aws.handlers.sagemaker_studio.SagemakerStudio.get_sagemaker_studio_domain',
            return_value={'DomainId': 'test'},
        )
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
