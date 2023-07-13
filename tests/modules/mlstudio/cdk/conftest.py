import pytest

from dataall.core.environment.db.models import Environment
from dataall.core.organizations.db.organization_models import Organization
from dataall.modules.mlstudio.db.models import SagemakerStudioUser
from dataall.db import models
from tests.cdkproxy.conftest import org, env


@pytest.fixture(scope='module', autouse=True)
def stack_org(db) -> Organization:
    yield org


@pytest.fixture(scope='module', autouse=True)
def stack_env(db, stack_org: Organization) -> Environment:
    yield env


@pytest.fixture(scope='module', autouse=True)
def sgm_studio(db, env: Environment) -> SagemakerStudioUser:
    with db.scoped_session() as session:
        sm_user = SagemakerStudioUser(
            label='thistable',
            owner='me',
            AWSAccountId=env.AwsAccountId,
            region=env.region,
            sagemakerStudioUserStatus='UP',
            sagemakerStudioUserName='ProfileName',
            sagemakerStudioUserNameSlugify='ProfileName',
            sagemakerStudioDomainID='domain',
            environmentUri=env.environmentUri,
            RoleArn=env.EnvironmentDefaultIAMRoleArn,
            SamlAdminGroupName='admins',
        )
        session.add(sm_user)
    yield sm_user
