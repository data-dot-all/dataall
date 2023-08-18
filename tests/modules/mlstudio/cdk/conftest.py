import pytest

from dataall.core.environment.db.environment_models import Environment
from dataall.core.organizations.db.organization_models import Organization
from dataall.modules.mlstudio.db.mlstudio_models import SagemakerStudioUser


@pytest.fixture(scope='module', autouse=True)
def sgm_studio(db, env_fixture: Environment) -> SagemakerStudioUser:
    with db.scoped_session() as session:
        sm_user = SagemakerStudioUser(
            label='thistable',
            owner='me',
            AWSAccountId=env_fixture.AwsAccountId,
            region=env_fixture.region,
            sagemakerStudioUserStatus='UP',
            sagemakerStudioUserName='ProfileName',
            sagemakerStudioUserNameSlugify='ProfileName',
            sagemakerStudioDomainID='domain',
            environmentUri=env_fixture.environmentUri,
            RoleArn=env_fixture.EnvironmentDefaultIAMRoleArn,
            SamlAdminGroupName=env_fixture.SamlGroupName,
        )
        session.add(sm_user)
    yield sm_user
