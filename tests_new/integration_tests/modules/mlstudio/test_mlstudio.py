from assertpy import assert_that

from integration_tests.errors import GqlError
from integration_tests.modules.mlstudio.queries import (
    list_smstudio_users,
    get_smstudio_user_presigned_url,
    get_environment_mlstudio_domain,
)


def test_create_smstudio_user(smstudio_user1):
    assert_that(smstudio_user1.stack.status).is_in('CREATE_COMPLETE', 'UPDATE_COMPLETE')


def test_list_smstudio_users(client1, client2, session_id, smstudio_user1):
    assert_that(list_smstudio_users(client1, term=session_id).nodes).is_length(1)
    assert_that(list_smstudio_users(client2, term=session_id).nodes).is_length(0)


def test_get_smstudio_user_presigned_url(client1, smstudio_user1):
    assert_that(get_smstudio_user_presigned_url(client1, smstudio_user1.sagemakerStudioUserUri)).starts_with('https://')


def test_get_smstudio_user_presigned_url_unauthorized(client2, smstudio_user1):
    assert_that(get_smstudio_user_presigned_url).raises(GqlError).when_called_with(
        client2, smstudio_user1.sagemakerStudioUserUri
    ).contains('UnauthorizedOperation', 'SGMSTUDIO_USER_URL')


def test_get_environment_mlstudio_domain(client1, smstudio_user1):
    assert_that(
        get_environment_mlstudio_domain(client1, smstudio_user1.environment.environmentUri).sagemakerStudioDomainName
    ).starts_with('dataall')
