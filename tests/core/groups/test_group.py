from unittest.mock import MagicMock


def mock_cognito_client(module_mocker):
    mock_cognito_client = MagicMock()
    module_mocker.patch('dataall.base.aws.cognito.Cognito', return_value=mock_cognito_client)
    mock_cognito_client().list_groups.return_value = ['cognitos', 'testadmins']
    return mock_cognito_client


def test_list_groups_env(client, env_fixture, group, module_mocker):
    cognito_client = mock_cognito_client(module_mocker)
    module_mocker.patch(
        'dataall.base.services.service_provider_factory.ServiceProviderFactory.get_service_provider_instance',
        return_value=cognito_client(),
    )
    response = client.query(
        """
        query listGroups (
          $filter: ServiceProviderGroupFilter
        ) {
          listGroups (
            filter: $filter
          ){
            groupName
          }
        }
        """,
        username='alice',
        filter={'type': 'environment', 'uri': env_fixture.environmentUri},
    )
    assert response.data.listGroups[0].groupName == 'cognitos'
