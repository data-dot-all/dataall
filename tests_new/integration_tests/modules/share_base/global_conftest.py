import pytest

from dataall.modules.shares_base.services.shares_enums import PrincipalType
from tests_new.integration_tests.modules.share_base.queries import (
    create_share_object,
    delete_share_object,
    get_share_object,
)


@pytest.fixture(scope='session')
def share1(client2, persistent_env1, group2):
    share1 = create_share_object(
        client=client2,
        dataset_or_item_params={'datasetUri': 'b56r7soc'},
        environmentUri=persistent_env1.environmentUri,
        groupUri=group2,
        principalId=group2,
        principalType=PrincipalType.Group.value,
        requestPurpose='test create share object',
        attachMissingPolicies=True,
    )
    share1 = get_share_object(client2, share1.shareUri)
    yield share1
    #delete_share_object(client2, share1.shareUri)


@pytest.fixture(scope='session')
def share2(client2, persistent_env1, group2):
    share2 = create_share_object(
        client=client2,
        dataset_or_item_params={'datasetUri': 'w0il0em5'},
        environmentUri=persistent_env1.environmentUri,
        groupUri=group2,
        principalId=group2,
        principalType=PrincipalType.Group.value,
        requestPurpose='test create share object',
        attachMissingPolicies=True,
    )
    share2 = get_share_object(client2, share2.shareUri)
    yield share2
    #delete_share_object(client2, share2.shareUri)
