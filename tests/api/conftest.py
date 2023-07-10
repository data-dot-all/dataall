from dataall.core.permissions.db.permission import Permission
from dataall.core.permissions.db.resource_policy import ResourcePolicy
from dataall.core.permissions.db.tenant import Tenant
from dataall.core.permissions.db.tenant_policy import TenantPolicy
from .client import *
from dataall.db import models


@pytest.fixture(scope='module', autouse=True)
def patch_request(module_mocker):
    """we will mock requests.post so no call to cdk proxy will be made"""
    module_mocker.patch('requests.post', return_value=True)


@pytest.fixture(scope='module', autouse=True)
def patch_check_env(module_mocker):
    module_mocker.patch(
        'dataall.api.Objects.Environment.resolvers.check_environment',
        return_value='CDKROLENAME',
    )
    module_mocker.patch(
        'dataall.api.Objects.Environment.resolvers.get_pivot_role_as_part_of_environment', return_value=False
    )


@pytest.fixture(scope='module', autouse=True)
def patch_es(module_mocker):
    module_mocker.patch('dataall.searchproxy.connect', return_value={})
    module_mocker.patch('dataall.searchproxy.search', return_value={})
    module_mocker.patch('dataall.searchproxy.base_indexer.BaseIndexer.delete_doc', return_value={})


@pytest.fixture(scope='module', autouse=True)
def patch_stack_tasks(module_mocker):
    module_mocker.patch(
        'dataall.aws.handlers.ecs.Ecs.is_task_running',
        return_value=False,
    )
    module_mocker.patch(
        'dataall.aws.handlers.ecs.Ecs.run_cdkproxy_task',
        return_value='arn:aws:eu-west-1:xxxxxxxx:ecs:task/1222222222',
    )
    module_mocker.patch(
        'dataall.aws.handlers.cloudformation.CloudFormation.describe_stack_resources',
        return_value=True,
    )


@pytest.fixture(scope='module', autouse=True)
def permissions(db):
    with db.scoped_session() as session:
        yield Permission.init_permissions(session)


@pytest.fixture(scope='module', autouse=True)
def user(db):
    with db.scoped_session() as session:
        user = dataall.db.models.User(userId='alice@test.com', userName='alice')
        session.add(user)
        yield user


@pytest.fixture(scope='module')
def group(db, user):
    with db.scoped_session() as session:
        group = dataall.db.models.Group(name='testadmins', label='testadmins', owner='alice')
        session.add(group)
        session.commit()
        yield group


@pytest.fixture(scope='module', autouse=True)
def user2(db):
    with db.scoped_session() as session:
        user = dataall.db.models.User(userId='bob@test.com', userName='bob')
        session.add(user)
        yield user


@pytest.fixture(scope='module')
def group2(db, user2):
    with db.scoped_session() as session:
        group = dataall.db.models.Group(name='dataengineers', label='dataengineers', owner=user2.userName)
        session.add(group)
        session.commit()
        yield group


@pytest.fixture(scope='module', autouse=True)
def user3(db):
    with db.scoped_session() as session:
        user = dataall.db.models.User(userId='david@test.com', userName='david')
        session.add(user)
        yield user


@pytest.fixture(scope='module')
def group3(db, user3):
    with db.scoped_session() as session:
        group = dataall.db.models.Group(name='datascientists', label='datascientists', owner=user3.userName)
        session.add(group)
        session.commit()
        yield group


@pytest.fixture(scope='module')
def group4(db, user3):
    with db.scoped_session() as session:
        group = dataall.db.models.Group(name='externals', label='externals', owner=user3.userName)
        session.add(group)
        session.commit()
        yield group


@pytest.fixture(scope='module')
def tenant(db, group, group2, permissions, user, user2, user3, group3, group4):
    with db.scoped_session() as session:
        tenant = Tenant.save_tenant(session, name='dataall', description='Tenant dataall')
        TenantPolicy.attach_group_tenant_policy(
            session=session,
            group=group.name,
            permissions=dataall.db.permissions.TENANT_ALL,
            tenant_name='dataall',
        )
        TenantPolicy.attach_group_tenant_policy(
            session=session,
            group=group2.name,
            permissions=dataall.db.permissions.TENANT_ALL,
            tenant_name='dataall',
        )
        TenantPolicy.attach_group_tenant_policy(
            session=session,
            group=group3.name,
            permissions=dataall.db.permissions.TENANT_ALL,
            tenant_name='dataall',
        )
        TenantPolicy.attach_group_tenant_policy(
            session=session,
            group=group4.name,
            permissions=dataall.db.permissions.TENANT_ALL,
            tenant_name='dataall',
        )
        yield tenant


@pytest.fixture(scope='module', autouse=True)
def env(client):
    cache = {}

    def factory(org, envname, owner, group, account, region, desc='test', parameters=None):
        if not parameters:
            parameters = {"dashboardsEnabled": "true"}

        key = f"{org.organizationUri}{envname}{owner}{''.join(group or '-')}{account}{region}"
        if cache.get(key):
            return cache[key]
        response = client.query(
            """mutation CreateEnv($input:NewEnvironmentInput){
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
                'vpcId': 'vpc-123456',
                'parameters': [{'key': k, 'value': v} for k, v in parameters.items()]
            },
        )
        cache[key] = response.data.createEnvironment
        return cache[key]

    yield factory


@pytest.fixture(scope="module")
def environment(db):
    def factory(
        organization: models.Organization,
        awsAccountId: str,
        label: str,
        owner: str,
        samlGroupName: str,
        environmentDefaultIAMRoleName: str,
    ) -> models.Environment:
        with db.scoped_session() as session:
            env = models.Environment(
                organizationUri=organization.organizationUri,
                AwsAccountId=awsAccountId,
                region="eu-central-1",
                label=label,
                owner=owner,
                tags=[],
                description="desc",
                SamlGroupName=samlGroupName,
                EnvironmentDefaultIAMRoleName=environmentDefaultIAMRoleName,
                EnvironmentDefaultIAMRoleArn=f"arn:aws:iam::{awsAccountId}:role/{environmentDefaultIAMRoleName}",
                CDKRoleArn=f"arn:aws::{awsAccountId}:role/EnvRole",
            )
            session.add(env)
            session.commit()
        return env

    yield factory


@pytest.fixture(scope="module")
def environment_group(db):
    def factory(
        environment: models.Environment,
        group: models.Group,
    ) -> models.EnvironmentGroup:
        with db.scoped_session() as session:

            env_group = models.EnvironmentGroup(
                environmentUri=environment.environmentUri,
                groupUri=group.name,
                environmentIAMRoleArn=environment.EnvironmentDefaultIAMRoleArn,
                environmentIAMRoleName=environment.EnvironmentDefaultIAMRoleName,
                environmentAthenaWorkGroup="workgroup",
            )
            session.add(env_group)
            ResourcePolicy.attach_resource_policy(
                session=session,
                resource_uri=environment.environmentUri,
                group=group.name,
                permissions=dataall.db.permissions.ENVIRONMENT_ALL,
                resource_type=dataall.db.models.Environment.__name__,
            )
            session.commit()
            return env_group

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
def org_fixture(org, user, group, tenant):
    org1 = org('testorg', user.userName, group.name)
    yield org1


@pytest.fixture(scope='module')
def env_fixture(env, org_fixture, user, group, tenant, module_mocker):
    module_mocker.patch('requests.post', return_value=True)
    module_mocker.patch('dataall.api.Objects.Environment.resolvers.check_environment', return_value=True)
    module_mocker.patch(
        'dataall.api.Objects.Environment.resolvers.get_pivot_role_as_part_of_environment', return_value=False
    )
    env1 = env(org_fixture, 'dev', 'alice', 'testadmins', '111111111111', 'eu-west-1')
    yield env1
