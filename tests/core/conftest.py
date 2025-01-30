import pytest

from dataall.core.environment.db.environment_models import Environment
from dataall.core.organizations.db.organization_models import Organization


@pytest.fixture(scope='module', autouse=True)
def env(client):
    cache = {}

    def factory(org, envname, owner, group, account, region, desc='test', parameters=None):
        if not parameters:
            parameters = {'dashboardsEnabled': 'true'}

        key = f'{org.organizationUri}{envname}{owner}{"".join(group or "-")}{account}{region}'
        if cache.get(key):
            return cache[key]
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
            username=f'{owner}',
            groups=[group],
            input={
                'label': f'{envname}',
                'description': f'{desc}',
                'organizationUri': org.organizationUri,
                'AwsAccountId': account,
                'tags': ['a', 'b', 'c'],
                'region': f'{region}',
                'SamlGroupName': f'{group}',
                'parameters': [{'key': k, 'value': v} for k, v in parameters.items()],
            },
        )
        cache[key] = response.data.createEnvironment
        return cache[key]

    yield factory


@pytest.fixture(scope='module')
def environment(db):
    def factory(
        organization: Organization,
        awsAccountId: str,
        label: str,
        owner: str,
        samlGroupName: str,
        environmentDefaultIAMRoleArn: str,
    ) -> Environment:
        with db.scoped_session() as session:
            env = Environment(
                organizationUri=organization.organizationUri,
                AwsAccountId=awsAccountId,
                region='eu-central-1',
                label=label,
                owner=owner,
                tags=[],
                description='desc',
                SamlGroupName=samlGroupName,
                EnvironmentDefaultIAMRoleName=environmentDefaultIAMRoleArn.split('/')[-1],
                EnvironmentDefaultIAMRoleArn=environmentDefaultIAMRoleArn,
                CDKRoleArn=f'arn:aws::{awsAccountId}:role/EnvRole',
            )
            session.add(env)
            session.commit()
        return env

    yield factory


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
def env_fixture(env, org_fixture, user, group, tenant, module_mocker):
    env1 = env(org_fixture, 'dev', 'alice', 'testadmins', '111111111111', 'eu-west-1')
    yield env1
