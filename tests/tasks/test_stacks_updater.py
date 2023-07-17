import pytest
from dataall.core.environment.db.models import Environment
from dataall.core.organizations.db.organization_models import Organization, OrganisationUserRole
from dataall.core.environment.tasks.env_stacks_updater import update_stacks


@pytest.fixture(scope='module', autouse=True)
def org(db):
    with db.scoped_session() as session:
        org = Organization(
            label='org',
            owner='alice',
            tags=[],
            description='desc',
            SamlGroupName='admins',
            userRoleInOrganization=OrganisationUserRole.Owner.value,
        )
        session.add(org)
    yield org


@pytest.fixture(scope='module', autouse=True)
def env(org, db):
    with db.scoped_session() as session:
        env = Environment(
            organizationUri=org.organizationUri,
            AwsAccountId='12345678901',
            region='eu-west-1',
            label='org',
            owner='alice',
            tags=[],
            description='desc',
            SamlGroupName='admins',
            EnvironmentDefaultIAMRoleName='EnvRole',
            EnvironmentDefaultIAMRoleArn='arn:aws::123456789012:role/EnvRole/GlueJobSessionRunner',
            CDKRoleArn='arn:aws::123456789012:role/EnvRole',
            userRoleInEnvironment='999',
        )
        session.add(env)
    yield env


def test_stacks_update(db, org, env, mocker):
    mocker.patch(
        'dataall.core.environment.tasks.env_stacks_updater.update_stack',
        return_value=True,
    )
    envs, others = update_stacks(engine=db, envname='local')
    assert envs == 1
    assert others == 0
