import uuid

from tests.core.permissions.test_permission import *


@pytest.fixture
def consumption_role(mock_aws_client, client, org_fixture, env_fixture, user, group, db):
    test_arn = f'arn:aws:sts::111111111111:assumed-role/Test/{str(uuid.uuid4())[:8]}'
    mock_aws_client.get_role.return_value = {'Role': {'Arn': test_arn}}
    query = """
        mutation addConsumptionRoleToEnvironment(
            $input:AddConsumptionRoleToEnvironmentInput!
        ){
            addConsumptionRoleToEnvironment(
                input:$input
            ){
                consumptionRoleUri
                consumptionRoleName
                environmentUri
                groupUri
                IAMRoleName
                IAMRoleArn
            }
        }
    """
    response = client.query(
        query,
        username=user,
        groups=[group.name],
        environmentUri=env_fixture.environmentUri,
        input={
            'consumptionRoleName': str(uuid.uuid4())[:8],
            'groupUri': str(uuid.uuid4())[:8],
            'IAMRoleArn': test_arn,
            'environmentUri': env_fixture.environmentUri,
            'dataallManaged': False,
        },
    )
    assert not response.errors
    return response
