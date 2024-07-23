import pytest

from dataall.core.environment.services.environment_service import EnvironmentService


@pytest.fixture(scope='module')
def env1(module_api_context_1, group1, org1, module_mocker):
    module_mocker.patch(
        'dataall.core.environment.services.environment_service.EnvironmentService.check_cdk_resources',
        return_value=True,
    )
    env = EnvironmentService.create_environment(
        uri=org1.organizationUri,
        data={
            'organizationUri': org1.organizationUri,
            'AwsAccountId': '111111111111',
            'region': 'us-east-1',
            'label': 'env1',
            'SamlGroupName': group1.name,
            'resourcePrefix': 'dataall'
        }
    )
    yield env