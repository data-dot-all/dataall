from unittest.mock import MagicMock


def test_list_groups_env(client, env_fixture, group, module_mocker):
    mock_client = MagicMock()
    module_mocker.patch(
        'dataall.base.aws.cognito.Cognito',
        return_value=mock_client
    )
    mock_client().list_groups.return_value = ['cognitos', 'testadmins']
    module_mocker.patch(
        'dataall.core.groups.api.resolvers.ServiceProviderFactory.get_service_provider_instance',
        return_value=mock_client()
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


