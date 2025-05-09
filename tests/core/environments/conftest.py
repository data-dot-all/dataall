import uuid

from dataall.core.environment.db.environment_enums import PolicyManagementOptions
from tests.core.permissions.test_permission import *


@pytest.fixture
def consumption_role(mock_aws_client, client, org_fixture, env_fixture, user, group, db):
    test_arn = f'arn:aws:sts::111111111111:role/Test/{str(uuid.uuid4())[:8]}'
    mock_aws_client.get_role.return_value = {'Role': {'Arn': test_arn}}
    query = """
        mutation addConsumptionRoleToEnvironment(
            $input:AddConsumptionRoleToEnvironmentInput!
        ){
            addConsumptionRoleToEnvironment(
                input:$input
            ){
                consumptionPrincipalUri
                consumptionPrincipalName
                environmentUri
                groupUri
                IAMPrincipalName
                IAMPrincipalArn
            }
        }
    """
    response = client.query(
        query,
        username=user,
        groups=[group.name],
        environmentUri=env_fixture.environmentUri,
        input={
            'consumptionPrincipalName': str(uuid.uuid4())[:8],
            'groupUri': str(uuid.uuid4())[:8],
            'IAMPrincipalArn': test_arn,
            'environmentUri': env_fixture.environmentUri,
            'dataallManaged': 'FULLY_MANAGED',
        },
    )
    assert not response.errors
    return response
