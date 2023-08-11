

def test_list_cognito_groups_env(client, env_fixture, group, module_mocker):
    module_mocker.patch(
        'dataall.core.cognito_groups.aws.cognito.Cognito.list_cognito_groups',
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
        filter={'type': 'environment', 'uri': env_fixture.environmentUri},
    )
    assert response.data.listCognitoGroups[0].groupName == 'cognitos'


