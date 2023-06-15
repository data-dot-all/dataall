import pytest

from dataall.modules.mlstudio.db.models import SagemakerStudioUser
from dataall.db import models
from tests.cdkproxy.conftest import org, env


@pytest.fixture(scope='module', autouse=True)
def stack_org(db) -> models.Organization:
    yield org


@pytest.fixture(scope='module', autouse=True)
def stack_env(db, stack_org: models.Organization) -> models.Environment:
    yield env


@pytest.fixture(scope='module', autouse=True)
def sgm_studio(db, env: models.Environment) -> SagemakerStudioUser:
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
