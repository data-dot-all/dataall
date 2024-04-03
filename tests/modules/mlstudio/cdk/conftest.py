import pytest

from dataall.core.environment.db.environment_models import Environment
from dataall.core.organizations.db.organization_models import Organization
from dataall.modules.mlstudio.db.mlstudio_models import SagemakerStudioUser, SagemakerStudioDomain


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


@pytest.fixture(scope='module', autouse=True)
def sgm_studio_domain(db, env_fixture: Environment) -> SagemakerStudioDomain:
    with db.scoped_session() as session:
        sm_domain = SagemakerStudioDomain(
            label='sagemaker-domain',
            owner='me',
            environmentUri=env_fixture.environmentUri,
            AWSAccountId=env_fixture.AwsAccountId,
            region=env_fixture.region,
            SagemakerStudioStatus='PENDING',
            DefaultDomainRoleName='DefaultMLStudioRole',
            sagemakerStudioDomainName='DomainName',
            vpcType='created',
            SamlGroupName=env_fixture.SamlGroupName,
        )
        session.add(sm_domain)
    yield sm_domain
