import pytest

import dataall
from dataall.db import permissions


@pytest.fixture(scope='module', autouse=True)
def org1(org, user, group, tenant):
    org1 = org('testorg', user.userName, group.name)
    yield org1


@pytest.fixture(scope='module', autouse=True)
def env1(env, org1, user, group, tenant, module_mocker):
    module_mocker.patch('requests.post', return_value=True)
    module_mocker.patch(
        'dataall.api.Objects.Environment.resolvers.check_environment', return_value=True
    )
    env1 = env(org1, 'dev', user.userName, group.name, '111111111111', 'eu-west-1')
    yield env1


def test_list_cognito_groups_env(client, env1, group, module_mocker):
    module_mocker.patch(
        'dataall.aws.handlers.cognito.Cognito.list_cognito_groups',
        return_value=[{"GroupName": 'cognitos'}, {"GroupName": 'testadmins'}],
    )
    response = client.query(
        """
        query listCognitoGroups (
          $filter: CognitoGroupFilter
        ) {
          listCognitoGroups (
            filter: $filter
          ){
            groupName
          }
        }
        """,
        username='alice',
        filter={'type': 'environment', 'uri': env1.environmentUri},
    )
    assert response.data.listCognitoGroups[0].groupName == 'cognitos'


