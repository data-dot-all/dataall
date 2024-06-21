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
        return_value='arn:aws:iam::1111111111:role/cdk-hnb659fds-lookup-role-1111111111-eu-west-1',
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
def sagemaker_studio_user(client, tenant, group, env_with_mlstudio) -> SagemakerStudioUser:
    response = client.query(
        """
            mutation createSagemakerStudioUser($input:NewSagemakerStudioUserInput!){
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
            'environmentUri': env_with_mlstudio.environmentUri,
        },
        username='alice',
        groups=[group.name],
    )
    yield response.data.createSagemakerStudioUser


@pytest.fixture(scope='module')
def multiple_sagemaker_studio_users(client, db, env_with_mlstudio, group):
    for i in range(0, 10):
        response = client.query(
            """
                mutation createSagemakerStudioUser($input:NewSagemakerStudioUserInput!){
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
                'environmentUri': env_with_mlstudio.environmentUri,
            },
            username='alice',
            groups=[group.name],
        )
        assert response.data.createSagemakerStudioUser.label == f'test{i}'
        assert response.data.createSagemakerStudioUser.SamlAdminGroupName == group.name
        assert response.data.createSagemakerStudioUser.environmentUri == env_with_mlstudio.environmentUri


@pytest.fixture(scope='module')
def env_with_mlstudio(client, org_fixture, user, group, parameters=None, vpcId='', subnetIds=[]):
    if not parameters:
        parameters = {'mlStudiosEnabled': 'True'}
    response = client.query(
        """mutation CreateEnv($input:NewEnvironmentInput!){
            createEnvironment(input:$input){
                organization{
                    organizationUri
                }
                environmentUri
                label
                AwsAccountId
                SamlGroupName
                region
                name
                owner
                parameters {
                    key
                    value
                }
            }
        }""",
        username=f'{user.username}',
        groups=['testadmins'],
        input={
            'label': f'dev',
            'description': '',
            'organizationUri': org_fixture.organizationUri,
            'AwsAccountId': '111111111111',
            'tags': [],
            'region': 'us-east-1',
            'SamlGroupName': 'testadmins',
            'parameters': [{'key': k, 'value': v} for k, v in parameters.items()],
            'vpcId': vpcId,
            'subnetIds': subnetIds,
        },
    )
    yield response.data.createEnvironment


@pytest.fixture(scope='module', autouse=True)
def org(client):
    cache = {}

    def factory(orgname, owner, group):
        key = orgname + owner + group
        if cache.get(key):
            print(f'returning item from cached key {key}')
            return cache.get(key)
        response = client.query(
            """mutation CreateOrganization($input:NewOrganizationInput){
                createOrganization(input:$input){
                    organizationUri
                    label
                    name
                    owner
                    SamlGroupName
                }
            }""",
            username=f'{owner}',
            groups=[group],
            input={
                'label': f'{orgname}',
                'description': f'test',
                'tags': ['a', 'b', 'c'],
                'SamlGroupName': f'{group}',
            },
        )
        cache[key] = response.data.createOrganization
        return cache[key]

    yield factory


@pytest.fixture(scope='module')
def org_fixture(org, user, group):
    org1 = org('testorg', user.username, group.name)
    yield org1


@pytest.fixture(scope='module')
def env_mlstudio_fixture(env, org_fixture, user, group, tenant):
    env1 = env_with_mlstudio(org_fixture, 'dev', 'alice', 'testadmins', '111111111111', 'eu-west-1')
    yield env1
