import pytest

from dataall.modules.mlstudio.db.mlstudio_models import SagemakerStudioUser, SagemakerStudioDomain


@pytest.fixture(scope='module', autouse=True)
def patch_aws_sagemaker_client(module_mocker):
    module_mocker.patch(
        'dataall.modules.mlstudio.services.mlstudio_service.get_sagemaker_studio_domain',
        return_value={'DomainId': 'test'},
    )


@pytest.fixture(scope='module', autouse=True)
def env_params():
    yield {'mlStudiosEnabled': 'True'}


@pytest.fixture(scope='module', autouse=True)
def get_cdk_look_up_role_arn(module_mocker):
    module_mocker.patch(
        'dataall.base.aws.sts.SessionHelper.get_cdk_look_up_role_arn',
        return_value="arn:aws:iam::1111111111:role/cdk-hnb659fds-lookup-role-1111111111-eu-west-1",
    )

@pytest.fixture(scope='module', autouse=True)
def check_default_vpc(module_mocker):
    module_mocker.patch(
        'dataall.base.aws.ec2_client.EC2.check_default_vpc_exists',
        return_value=False,
    )


@pytest.fixture(scope='module', autouse=True)
def check_vpc_exists(module_mocker):
    module_mocker.patch(
        'dataall.base.aws.ec2_client.EC2.check_vpc_exists',
        return_value=True,
    )


@pytest.fixture(scope='module')
def sagemaker_studio_domain(client, group, env_fixture) -> SagemakerStudioDomain:
    response = client.query(
        """
            mutation createMLStudioDomain($input: NewStudioDomainInput) {
              createMLStudioDomain(input: $input) {
                sagemakerStudioUri
                environmentUri
                label
                vpcType
                vpcId
                subnetIds
              }
            }
            """,
        input={
            'label': 'testcreate',
            'environmentUri': env_fixture.environmentUri,
        },
        username='alice',
        groups=[group.name],
    )
    yield response.data.createMLStudioDomain


@pytest.fixture(scope='module')
def sagemaker_studio_domain_with_vpc(client, group, env_fixture) -> SagemakerStudioDomain:
    response = client.query(
        """
            mutation createMLStudioDomain($input: NewStudioDomainInput) {
              createMLStudioDomain(input: $input) {
                sagemakerStudioUri
                environmentUri
                label
                vpcType
                vpcId
                subnetIds
              }
            }
            """,
        input={
            'label': 'testcreate',
            'environmentUri': env_fixture.environmentUri,
            'vpcId': 'vpc-12345',
            'subnetIds': ['subnet-12345', 'subnet-67890']
        },
        username='alice',
        groups=[group.name],
    )

    yield response.data.createMLStudioDomain


@pytest.fixture(scope='module')
def sagemaker_studio_user(client, tenant, group, env_fixture, sagemaker_studio_domain) -> SagemakerStudioUser:
    response = client.query(
        """
            mutation createSagemakerStudioUser($input:NewSagemakerStudioUserInput){
            createSagemakerStudioUser(input:$input){
                sagemakerStudioUserUri
                name
                label
                created
                description
                SamlAdminGroupName
                environmentUri
                tags
            }
        }
            """,
        input={
            'label': 'testcreate',
            'SamlAdminGroupName': group.name,
            'environmentUri': env_fixture.environmentUri,
        },
        username='alice',
        groups=[group.name],
    )
    yield response.data.createSagemakerStudioUser


@pytest.fixture(scope='module')
def multiple_sagemaker_studio_users(client, db, env_fixture, group):
        for i in range(0, 10):
            response = client.query(
                """
                mutation createSagemakerStudioUser($input:NewSagemakerStudioUserInput){
                createSagemakerStudioUser(input:$input){
                    sagemakerStudioUserUri
                    name
                    label
                    created
                    description
                    SamlAdminGroupName
                    environmentUri
                    tags
                }
            }
                """,
                input={
                    'label': f'test{i}',
                    'SamlAdminGroupName': group.name,
                    'environmentUri': env_fixture.environmentUri,
                },
                username='alice',
                groups=[group.name],
            )
            assert response.data.createSagemakerStudioUser.label == f'test{i}'
            assert (
                    response.data.createSagemakerStudioUser.SamlAdminGroupName
                    == group.name
            )
            assert (
                    response.data.createSagemakerStudioUser.environmentUri
                    == env_fixture.environmentUri
            )
