
from dataall.modules.shares_base.services.shares_enums import PrincipalType
from tests_new.integration_tests.modules.shares.queries import create_share_object


def test_create_share_object(client1, session_env1, session_s3_dataset1, group2):
    test_object = create_share_object(
        client=client1,
        dataset_or_item_params={"datasetUri":session_s3_dataset1.datasetUri},
        environmentUri=session_env1.environmentUri,
        groupUri=group2,
        principalId=group2,
        principalType=PrincipalType.Group,
        requestPurpose='test create share object',
        attachMissingPolicies=True
    )
