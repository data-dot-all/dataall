import pytest
from  tests.core.conftest import *


@pytest.fixture(scope='module', autouse=True)
def patch_es(module_mocker):
    module_mocker.patch('dataall.base.searchproxy.connect', return_value={})
    module_mocker.patch('dataall.base.searchproxy.search', return_value={})
    module_mocker.patch('dataall.modules.catalog.indexers.base_indexer.BaseIndexer.delete_doc', return_value={})
    module_mocker.patch('dataall.modules.catalog.indexers.base_indexer.BaseIndexer._index', return_value={})


@pytest.fixture(scope="module")
def environment_group(db):
    def factory(
        environment: Environment,
        group: Group,
    ) -> EnvironmentGroup:
        with db.scoped_session() as session:
            env_group = EnvironmentGroup(
                environmentUri=environment.environmentUri,
                groupUri=group.name,
                environmentIAMRoleArn=environment.EnvironmentDefaultIAMRoleArn,
                environmentIAMRoleName=environment.EnvironmentDefaultIAMRoleName,
                environmentAthenaWorkGroup="workgroup",
            )
            session.add(env_group)
            session.commit()
            ResourcePolicy.attach_resource_policy(
                session=session,
                resource_uri=environment.environmentUri,
                group=group.name,
                permissions=ENVIRONMENT_ALL,
                resource_type=Environment.__name__,
            )
            session.commit()
            return env_group

    yield factory


@pytest.fixture(scope='module', autouse=True)
def org_fixture(org, user, group, tenant):
    yield org('testorg', user.username, group.name)


@pytest.fixture(scope='module', autouse=True)
def env_fixture(env, org_fixture, user, group, tenant, module_mocker, patch_stack_tasks):
    yield env(org_fixture, 'dev', user.username, group.name, '111111111111', 'eu-west-1')