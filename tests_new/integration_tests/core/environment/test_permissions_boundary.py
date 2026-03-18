import logging

from assertpy import assert_that

from integration_tests.aws_clients.iam import IAMClient
from integration_tests.aws_clients.sts import STSClient
from integration_tests.core.environment.queries import get_environment, update_environment
from integration_tests.core.environment.global_conftest import create_env

log = logging.getLogger(__name__)

BOUNDARY_ARN = 'arn:aws:iam::aws:policy/PowerUserAccess'


def test_create_environment_with_permissions_boundary(client1, group1, org1, testdata):
    envdata = testdata.envs['temp_env1']
    with create_env(
        client1,
        'boundary_test_env',
        group1,
        org1.organizationUri,
        envdata.accountId,
        envdata.region,
        PermissionsBoundaryPolicyArn=BOUNDARY_ARN,
    ) as env:
        assert_that(env.PermissionsBoundaryPolicyArn).is_equal_to(BOUNDARY_ARN)

        # Verify the IAM role in AWS has the boundary attached
        role_arn = f'arn:aws:iam::{env.AwsAccountId}:role/dataall-integration-tests-role-{env.region}'
        session = STSClient(role_arn=role_arn, region=env.region).get_refreshable_session()
        iam_client = IAMClient(session=session, region=env.region)
        role = iam_client.get_role(env.EnvironmentDefaultIAMRoleName)
        assert_that(role['Role']['PermissionsBoundary']['PermissionsBoundaryArn']).is_equal_to(BOUNDARY_ARN)


def test_update_environment_permissions_boundary(client1, session_env1):
    env_uri = session_env1.environmentUri

    updated = update_environment(client1, env_uri, {'PermissionsBoundaryPolicyArn': BOUNDARY_ARN})
    assert_that(updated.PermissionsBoundaryPolicyArn).is_equal_to(BOUNDARY_ARN)

    fetched = get_environment(client1, env_uri)
    assert_that(fetched.PermissionsBoundaryPolicyArn).is_equal_to(BOUNDARY_ARN)

    # Clear boundary
    update_environment(client1, env_uri, {'PermissionsBoundaryPolicyArn': ''})
