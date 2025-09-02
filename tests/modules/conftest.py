from typing import Dict

import pytest

from dataall.core.environment.db.environment_models import Environment, EnvironmentGroup, EnvironmentParameter
from dataall.core.organizations.db.organization_models import Organization
from dataall.core.permissions.services.environment_permissions import ENVIRONMENT_ALL
from dataall.core.permissions.services.organization_permissions import ORGANIZATION_ALL
from dataall.core.permissions.services.resource_policy_service import ResourcePolicyService
from dataall.core.stacks.db.stack_repositories import StackRepository
from dataall.core.stacks.db.stack_models import KeyValueTag


@pytest.fixture(scope='module', autouse=True)
def patch_es(module_mocker):
    module_mocker.patch('dataall.base.searchproxy.connect', return_value={})
    module_mocker.patch('dataall.base.searchproxy.search', return_value={})
    module_mocker.patch('dataall.modules.catalog.indexers.base_indexer.BaseIndexer.delete_doc', return_value={})
    module_mocker.patch('dataall.modules.catalog.indexers.base_indexer.BaseIndexer._index', return_value={})


@pytest.fixture(scope='module')
def environment_group(db):
    def factory(environment: Environment, group: str) -> EnvironmentGroup:
        with db.scoped_session() as session:
            env_group = EnvironmentGroup(
                environmentUri=environment.environmentUri,
                groupUri=group,
                environmentIAMRoleArn=environment.EnvironmentDefaultIAMRoleArn,
                environmentIAMRoleName=environment.EnvironmentDefaultIAMRoleName,
                environmentAthenaWorkGroup='workgroup',
            )
            session.add(env_group)
            session.commit()
            ResourcePolicyService.attach_resource_policy(
                session=session,
                resource_uri=environment.environmentUri,
                group=group,
                permissions=ENVIRONMENT_ALL,
                resource_type=Environment.__name__,
            )
            session.commit()
            return env_group

    yield factory


def _create_env_params(session, env: Environment, params: Dict[str, str]):
    if params:
        for key, value in params.items():
            param = EnvironmentParameter(
                env_uri=env.environmentUri,
                key=key,
                value=value,
            )
            session.add(param)
        session.commit()


def _create_env_stack(session, env):
    tags = KeyValueTag(
        targetType='environment',
        targetUri=env.environmentUri,
        key='CREATOR',
        value='customtagowner',
    )
    session.add(tags)

    StackRepository.create_stack(
        session=session,
        environment_uri=env.environmentUri,
        target_type='environment',
        target_uri=env.environmentUri,
    )


@pytest.fixture(scope='module', autouse=True)
def env(db, environment_group):
    def factory(
        org,
        envname,
        owner,
        group,
        account,
        region='eu-west-1',
        desc='test',
        role='iam_role',
        parameters=None,
        envUri=None,
    ):
        with db.scoped_session() as session:
            kwargs = {'environmentUri': envUri} if envUri else {}
            env = Environment(
                organizationUri=org.organizationUri,
                AwsAccountId=account,
                region=region,
                label=envname,
                owner=owner,
                tags=[],
                description=desc,
                SamlGroupName=group,
                EnvironmentDefaultIAMRoleName=role,
                EnvironmentDefaultIAMRoleArn=f'arn:aws:iam::{account}:role/{role}',
                EnvironmentDefaultBucketName='defaultbucketname1234567789',
                EnvironmentLogsBucketName='logsbucketname1234567789',
                CDKRoleArn=f'arn:aws::{account}:role/EnvRole',
                EnvironmentDefaultAthenaWorkGroup='DefaultWorkGroup',
                **kwargs,
            )
            session.add(env)
            session.commit()
            _create_env_params(session, env, parameters)
            _create_env_stack(session, env)

        return env

    yield factory


@pytest.fixture(scope='module', autouse=True)
def org(db):
    def factory(name, group, user):
        with db.scoped_session() as session:
            org = Organization(
                label=name,
                name=name,
                description=name,
                owner=user.username,
                SamlGroupName=group.name,
            )
            session.add(org)
            session.commit()
            ResourcePolicyService.attach_resource_policy(
                session=session,
                resource_uri=org.organizationUri,
                group=group.name,
                permissions=ORGANIZATION_ALL,
                resource_type=Organization.__name__,
            )
            session.commit()
            return org

    yield factory


@pytest.fixture(scope='module')
def org_fixture(org, group, user):
    return org('testorg', group, user)


@pytest.fixture(scope='module')
def env_params():
    # Can be overridden in the submodules
    return {}


@pytest.fixture(scope='module')
def env_fixture(env, environment_group, org_fixture, user, group, tenant, env_params):
    env1 = env(org_fixture, 'dev', 'alice', 'testadmins', '111111111111', parameters=env_params)
    environment_group(env1, group.name)
    yield env1
